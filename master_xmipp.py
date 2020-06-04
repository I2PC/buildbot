import re

from buildbot.plugins import util, steps
from buildbot.steps.shell import ShellCommand, SetProperty
from buildbot.config import BuilderConfig
from buildbot.schedulers import triggerable
from buildbot.schedulers.forcesched import ForceScheduler

import settings
from settings import (WORKER,  XMIPP_SLACK_CHANNEL,
                      XMIPP_TESTS, XMIPP_BUNDLE_TESTS, EMAN212,
                      FORCE_BUILDER_PREFIX, PROD_GROUP_ID,
                      LD_LIBRARY_PATH, timeOutShort, SDEVEL_GROUP_ID,
                      SPROD_GROUP_ID, PROD_LD_LIBRARY_PATH, PROD_SCIPION_CMD,
                      XMIPP_INSTALL_PREFIX)
from common_utils import GenerateStagesCommand
from master_scipion import pluginFactory, xmippPluginData


# #############################################################################
# ########################## COMMANDS & UTILS #################################
# #############################################################################
def xmippBashrc2Dict(rc, stdout, stderr):
    vars = {}
    for l in stdout.split('\n'):
        r = re.match('export (.*)=(.*)', l)
        if r:
            vars[r.group(1)] = r.group(2)
    return vars


def glob2list(rc, stdout, stderr):
    ''' Function used as the extrat_fn function for SetProperty class
        This takes the output from env command and creates a dictionary of
        the environment, the result of which is stored in a property names
        env'''
    if not rc:
        env_list = [l.strip() for l in stdout.split('\n')]
        env_dict = {l.split('=', 1)[0]: l.split('=', 1)[1] for l in
                    env_list if len(l.split('=', 1)) == 2}
        return {'env': env_dict}


# *****************************************************************************
#                         XMIPP BUNDLE FACTORY
# *****************************************************************************
def xmippBundleFactory(groupId):
    xmippTestSteps = util.BuildFactory()
    xmippTestSteps.workdir = settings.SDEVEL_XMIPP_HOME
    if groupId != SDEVEL_GROUP_ID:
        xmippTestSteps.addStep(SetProperty(command=["bash", "-c", "source build/xmipp.bashrc; env"],
                                           extract_fn=glob2list,
                                           env={"SCIPION_HOME": util.Property("SCIPION_HOME"),
                                                "SCIPION_LOCAL_CONFIG": util.Property("SCIPION_LOCAL_CONFIG"),
                                                "LD_LIBRARY_PATH": LD_LIBRARY_PATH}))

        xmippTestSteps.addStep(
            GenerateStagesCommand(command=["./xmipp", "test", "--show"],
                                  name="Generate test stages for Xmipp programs",
                                  description="Generating test stages for Xmipp programs",
                                  descriptionDone="Generate test stages for Xmipp programs",
                                  haltOnFailure=False,
                                  pattern='./xmipp test (.*)',
                                  rootName='xmipp',
                                  env=util.Property('env')))

        xmippTestSteps.addStep(
            GenerateStagesCommand(command=["./xmipp", "test", "--show"],
                                  name="Generate test stages for Xmipp functions",
                                  description="Generating test stages for Xmipp functions",
                                  descriptionDone="Generate test stages for Xmipp functions",
                                  haltOnFailure=False,
                                  pattern='xmipp_test_(.*)',
                                  rootName='xmipp',
                                  env=util.Property('env')))
    else:
        xmippTestSteps.addStep(SetProperty(
            command=["bash", "-c", "cd " + settings.EM_ROOT + " ; " + "source xmipp/xmipp.bashrc; env"],
            extract_fn=glob2list,
            env={"SCIPION_HOME": util.Property("SCIPION_HOME"),
                 "SCIPION_LOCAL_CONFIG": util.Property("SCIPION_LOCAL_CONFIG"),
                 "LD_LIBRARY_PATH": LD_LIBRARY_PATH,
                 "EM_ROOT": settings.EM_ROOT}))

        xmippTestShowcmd = ["bash", "-c", "cd " + settings.SDEVEL_XMIPP_HOME + " ; " + "./xmipp test --show"]
        xmippTestSteps.addStep(
            GenerateStagesCommand(command=xmippTestShowcmd,
                                  name="Generate test stages for Xmipp programs",
                                  description="Generating test stages for Xmipp programs",
                                  descriptionDone="Generate test stages for Xmipp programs",
                                  haltOnFailure=False,
                                  rootName=settings.XMIPP_CMD,
                                  pattern='./xmipp test (.*)',
                                  env=util.Property('env')))

    return xmippTestSteps


# *****************************************************************************
#                         XMIPP TEST FACTORY IN SCIPION
# *****************************************************************************
def xmippTestFactory(groupId):
    xmippTestSteps = util.BuildFactory()
    xmippTestSteps.workdir = util.Property('SCIPION_HOME')
    xmippTestSteps.addStep(ShellCommand(command=['echo', 'SCIPION_HOME: ', util.Property('SCIPION_HOME')],
                     name='Echo scipion home',
                     description='Echo scipion home',
                     descriptionDone='Echo scipion home',
                     timeout=timeOutShort))
    # add TestRelionExtractStreaming manually because it needs eman 2.12
    gpucorrclassifiers = ["xmipp3.tests.test_protocols_gpuCorr_classifier.TestGpuCorrClassifier",
                          "xmipp3.tests.test_protocols_gpuCorr_semiStreaming.TestGpuCorrSemiStreaming",
                          "xmipp3.tests.test_protocols_gpuCorr_fullStreaming.TestGpuCorrFullStreaming"]

    envs = {gpucorrcls: EMAN212 for gpucorrcls in gpucorrclassifiers}

    if groupId != SDEVEL_GROUP_ID:
        scipionCmd = "./scipion3"
        if groupId == SPROD_GROUP_ID:
            scipionCmd = PROD_SCIPION_CMD
        xmippTestSteps.addStep(
            GenerateStagesCommand(command=[scipionCmd, "test", "--show", "--grep", "xmipp3", "--mode", "onlyclasses"],
                                  name="Generate Scipion test stages for Xmipp",
                                  description="Generating Scipion test stages for Xmipp",
                                  descriptionDone="Generate Scipion test stages for Xmipp",
                                  haltOnFailure=False,
                                  stagePrefix=[scipionCmd, "test"],
                                  targetTestSet='xmipp3',
                                  stageEnvs=envs))

    else:

        xmippTestShowcmd = ["bash", "-c", "./scipion3 test --show --grep xmipp3 --mode onlyclasses"]

        xmippTestSteps.addStep(
            GenerateStagesCommand(
                command=xmippTestShowcmd,
                name="Generate Scipion test stages for Xmipp",
                description="Generating Scipion test stages for Xmipp",
                descriptionDone="Generate Scipion test stages for Xmipp",
                haltOnFailure=False,
                stagePrefix=[settings.SCIPION_CMD, "test"],
                targetTestSet='xmipp3',
                rootName='scipion3',
                stageEnvs=envs))

    return xmippTestSteps


# #############################################################################
# ############################## BUILDERS #####################################
# #############################################################################

def getXmippBuilders(groupId):
    builders = []
    props = {'slackChannel': XMIPP_SLACK_CHANNEL}
    env = {
        "SCIPION_IGNORE_PYTHONPATH": "True",
        "SCIPION_LOCAL_CONFIG": util.Property("SCIPION_LOCAL_CONFIG"),
        "SCIPION_HOME": util.Property('SCIPION_HOME')
    }
    cudaEnv = {'PATH': ["/usr/local/cuda/bin", "${PATH}"]}
    cudaEnv.update(env)
    installEnv = {'SCIPION_HOME': util.Property('SCIPION_HOME')}
    installEnv.update(cudaEnv)
    bundleEnv = {}
    bundleEnv.update(cudaEnv)
    bundleEnv.update(installEnv)

    if groupId == PROD_GROUP_ID:
        extraBinaries = []
        if groupId == PROD_GROUP_ID:
            extraBinaries = ['xmippSrc', 'deepLearningToolkit', 'nma']
        builders.append(
            BuilderConfig(name=XMIPP_INSTALL_PREFIX + groupId,
                          workernames=[WORKER],
                          tags=[groupId],
                          factory=pluginFactory(groupId, 'scipion-em-xmipp', shortname='xmipp3', doTest=False,
                                                extraBinaries=extraBinaries),
                          workerbuilddir=groupId,
                          env=env,
                          properties=props)
        )

        builders.append(
            BuilderConfig(name="%s%s" % (XMIPP_TESTS, groupId),
                          tags=[groupId, XMIPP_TESTS],
                          workernames=[WORKER],
                          factory=pluginFactory(groupId,'scipion-em-xmipp', shortname='xmipp3', doInstall=False),
                          workerbuilddir=groupId,
                          properties={'slackChannel': xmippPluginData.get('slackChannel', "")},
                          env=env)
        )

    elif groupId == SDEVEL_GROUP_ID or groupId == SPROD_GROUP_ID:

        env = {
            "SCIPION_IGNORE_PYTHONPATH": "True",
            "SCIPION_LOCAL_CONFIG": util.Property("SCIPION_LOCAL_CONFIG"),
            "SCIPION_HOME": util.Property('SCIPION_HOME'),
            "LD_LIBRARY_PATH": LD_LIBRARY_PATH,
            "EM_ROOT": settings.EM_ROOT
        }
        if groupId == SPROD_GROUP_ID:
            env['EM_ROOT'] = settings.SPROD_EM_ROOT
            env['LD_LIBRARY_PATH'] = PROD_LD_LIBRARY_PATH

        builders.append(
            BuilderConfig(name=XMIPP_TESTS + groupId,
                          tags=[groupId],
                          workernames=[WORKER],
                          factory=xmippTestFactory(groupId),
                          workerbuilddir=groupId,
                          properties=props,
                          env=env)
        )

        if groupId == SDEVEL_GROUP_ID:
            bundleEnv.update(env)
            builders.append(
                BuilderConfig(name=XMIPP_BUNDLE_TESTS + groupId,
                              tags=[groupId],
                              workernames=[WORKER],
                              factory=xmippBundleFactory(groupId),
                              workerbuilddir=groupId,
                              env=bundleEnv,
                              properties=props)
            )

    return builders


# #############################################################################
# ############################## SCHEDULERS ###################################
# #############################################################################

def getXmippSchedulers(groupId):

    xmippSchedulerNames = [XMIPP_TESTS + groupId]
    if groupId == PROD_GROUP_ID:
        xmippSchedulerNames += [XMIPP_INSTALL_PREFIX + groupId]

    if groupId == SDEVEL_GROUP_ID:
        xmippSchedulerNames.append(XMIPP_BUNDLE_TESTS + groupId)
    schedulers = []
    for name in xmippSchedulerNames:
        schedulers.append(
            triggerable.Triggerable(name=name,
                                    builderNames=[name]))
        forceScheduler = '%s%s' % (FORCE_BUILDER_PREFIX, name)
        schedulers.append(
            ForceScheduler(name=forceScheduler,
                           builderNames=[name]))
    return schedulers
