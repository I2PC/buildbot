import os
import re

from buildbot.plugins import util, steps
from buildbot.steps.shell import ShellCommand, SetProperty
from buildbot.config import BuilderConfig
from buildbot.schedulers import triggerable
from buildbot.schedulers.forcesched import ForceScheduler
from buildbot.steps.source.git import Git

import settings
from settings import (WORKER, XMIPP_SLACK_CHANNEL,
                      XMIPP_TESTS, XMIPP_BUNDLE_TESTS, EMAN212,
                      FORCE_BUILDER_PREFIX, PROD_GROUP_ID,
                      LD_LIBRARY_PATH, timeOutShort, SDEVEL_GROUP_ID,
                      SPROD_GROUP_ID, PROD_LD_LIBRARY_PATH, PROD_SCIPION_CMD,
                      XMIPP_INSTALL_PREFIX, XMIPP_DOCS_PREFIX, WORKER1)
from common_utils import GenerateStagesCommand, changeConfVar
from master_scipion import pluginFactory, xmippPluginData, ScipionCommandStep


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

    env = {"SCIPION_HOME": util.Property("SCIPION_HOME"),
           "SCIPION_LOCAL_CONFIG": util.Property("SCIPION_LOCAL_CONFIG"),
           "LD_LIBRARY_PATH": LD_LIBRARY_PATH,
           "EM_ROOT": settings.EM_ROOT}

    xmippTestSteps.addStep(SetProperty(command=["bash", "-c", "source build/xmipp.bashrc; env"],
                                       extract_fn=glob2list,
                                       env=env))

    xmippTestSteps.addStep(
        GenerateStagesCommand(command=["./xmipp", "test", "--show"],
                              name="Generate test stages for Xmipp programs",
                              description="Generating test stages for Xmipp programs",
                              descriptionDone="Generate test stages for Xmipp programs",
                              haltOnFailure=False,
                              pattern='./xmipp test (.*)',
                              rootName=settings.XMIPP_CMD,
                              timeout=settings.timeOutExecute,
                              blacklist=settings.SCIPION_TESTS_BLACKLIST,
                              env=util.Property('env')))

    xmippTestSteps.addStep(
        GenerateStagesCommand(command=["./xmipp", "test", "--show"],
                              name="Generate test stages for Xmipp functions",
                              description="Generating test stages for Xmipp functions",
                              descriptionDone="Generate test stages for Xmipp functions",
                              haltOnFailure=False,
                              timeout=settings.timeOutExecute,
                              pattern='xmipp_test_(.*)',
                              rootName=settings.XMIPP_CMD,
                              blacklist=settings.SCIPION_TESTS_BLACKLIST,
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

    if groupId == PROD_GROUP_ID:
        scipionCmd = "./scipion"
        xmippTestSteps.addStep(
            GenerateStagesCommand(command=[scipionCmd, "test", "--show", "--grep", "xmipp3", "--mode", "onlyclasses"],
                                  name="Generate Scipion test stages for Xmipp",
                                  description="Generating Scipion test stages for Xmipp",
                                  descriptionDone="Generate Scipion test stages for Xmipp",
                                  haltOnFailure=False,
                                  stagePrefix=[scipionCmd, "test"],
                                  targetTestSet='xmipp3',
                                  timeout=settings.timeOutExecute,
                                  blacklist=settings.SCIPION_TESTS_BLACKLIST,
                                  stageEnvs=envs))

    else:

        deepLearningToolkitCmd = ["bash", "-c", "./scipion3 installb deepLearningToolkit"]
        xmippTestSteps.addStep(ShellCommand(command=deepLearningToolkitCmd,
                                            name='Installing deepLearningToolkit',
                                            description='Installing deepLearningToolkit',
                                            descriptionDone='Installing deepLearningToolkit',
                                            timeout=timeOutShort))

        nmaCmd = ["bash", "-c", "./scipion3 installb nma"]
        xmippTestSteps.addStep(ShellCommand(command=nmaCmd,
                                            name='Installing nma',
                                            description='Installing nma',
                                            descriptionDone='Installing nma',
                                            timeout=timeOutShort))

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
                timeout=settings.timeOutExecute,
                blacklist=settings.SCIPION_TESTS_BLACKLIST,
                stageEnvs=envs))

    return xmippTestSteps

# *****************************************************************************
#                         DOCS FACTORY
# *****************************************************************************


def docsFactory(groupId):
    factorySteps = util.BuildFactory()
    factorySteps.workdir = settings.XMIPP_SDEVEL_DOCS_ROOT

    if groupId == settings.SDEVEL_GROUP_ID:
        folderNames = ['xmippDoc', 'xmippPythonDoc', 'xmippJavaDoc']
        docsRepos = [settings.XMIPP_SDEVEL_C_DOCS_REPO,
                     settings.XMIPP_SDEVEL_PY_DOCS_REPO,
                     settings.XMIPP_SDEVEL_JAR_DOCS_REPO]


        for i in range(3):
            # Remove all API documentation
            factorySteps.addStep(
                ShellCommand(command='rm -rf ' + folderNames[i],
                             name='Remove ' + folderNames[i],
                             description='Remove ' + folderNames[i],
                             descriptionDone='Remove ' + folderNames[i],
                             timeout=settings.timeOutInstall))

            # Select gh-pages branch for the three repositories
            # Clone the documentation repositories
            factorySteps.addStep(
                ShellCommand(
                    command='git clone --branch gh-pages ' + docsRepos[i],
                    name= folderNames[i] + 'API repository pull',
                    description=folderNames[i] + 'API repository pull',
                    descriptionDone=folderNames[i] + ' API repository pull',
                    timeout=settings.timeOutInstall))

            factorySteps.addStep(
                ShellCommand(command='rm -rf ' + folderNames[i] + '/html',
                             name='Remove the ' + folderNames[i] + ' API folder',
                             description='Remove the ' + folderNames[i] + ' API folder',
                             descriptionDone='Remove the ' + folderNames[i] + ' API folder',
                             timeout=settings.timeOutInstall))

            factorySteps.addStep(
                ShellCommand(command=["bash", "-c", "cd " + folderNames[i] + "&& git add ."],
                             name='Git add deleted ' + folderNames[i] + ' API docs',
                             description='Git add deleted ' + folderNames[i] + ' API docs',
                             descriptionDone='Git add deleted ' + folderNames[i] + ' API docs',
                             timeout=settings.timeOutInstall))

            factorySteps.addStep(ShellCommand(
                command=["bash", "-c",
                         "cd " + folderNames[i] + " && git commit -m \'buildbot automated-update\'"],
                name='Git commit ' + folderNames[i] + ' API docs',
                description='Git commit  ' + folderNames[i] + ' API docs',
                descriptionDone='Git commit ' + folderNames[i] + ' API docs',
                timeout=settings.timeOutInstall,
                haltOnFailure=False))

            factorySteps.addStep(
                ShellCommand(command=["bash", "-c", "cd " + folderNames[i] + " && git push"],
                             name='Git push ' + folderNames[i] + ' API docs to repo',
                             description='Git push  ' + folderNames[i] + ' API docs to repo',
                             descriptionDone='Git push  ' + folderNames[i] + ' API docs to repo',
                             timeout=settings.timeOutInstall,
                             haltOnFailure=False))

            # Generate API documentation
            updatingDocCmd = "cd " + folderNames[i] + " && doxygen Doxyfile"

            factorySteps.addStep(
                ScipionCommandStep(command=updatingDocCmd,
                             name='Updating the ' + folderNames[i] + ' API documentation',
                             description='Updating the ' + folderNames[i] + ' API documentation',
                             descriptionDone='Updating the ' + folderNames[i] + ' API documentation',
                             timeout=settings.timeOutInstall))

            # Upload the repositories
            uploadDocCmd = ('cd ' + folderNames[i] +
                            ' ; git add .  ; '
                            'git commit -m "buildbot automated-update" ; '
                            'git push')

            factorySteps.addStep(
                ScipionCommandStep(command=uploadDocCmd,
                                   name='Uploading the ' + folderNames[i] + ' API documentation',
                                   description='Uploading the ' + folderNames[i] + ' API documentation',
                                   descriptionDone='Uploading the ' + folderNames[i] + ' API documentation',
                                   timeout=settings.timeOutInstall))

    return factorySteps

# #############################################################################
# ############################## BUILDERS #####################################
# #############################################################################

def getXmippBuilders(groupId):
    builders = []
    props = {'slackChannel': XMIPP_SLACK_CHANNEL}
    env = {
        "SCIPION_IGNORE_PYTHONPATH": "True",
        "SCIPION_LOCAL_CONFIG": util.Property("SCIPION_LOCAL_CONFIG"),
        "SCIPION_HOME": util.Property('SCIPION_HOME'),
        "PROT_LOGS_LAST_LINES": settings.PROT_LOGS_LAST_LINES
    }
    cudaEnv = {'PATH': [settings.CUDA_BIN, "${PATH}"]}
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
            "EM_ROOT": settings.EM_ROOT,
            "PROT_LOGS_LAST_LINES": settings.PROT_LOGS_LAST_LINES
        }
        if groupId == SPROD_GROUP_ID:
            env['EM_ROOT'] = settings.SPROD_EM_ROOT
            env['LD_LIBRARY_PATH'] = PROD_LD_LIBRARY_PATH

        worker = WORKER if groupId == SPROD_GROUP_ID else WORKER1
        builders.append(
            BuilderConfig(name=XMIPP_TESTS + groupId,
                          tags=[groupId],
                          workernames=[worker],
                          factory=xmippTestFactory(groupId),
                          workerbuilddir=groupId,
                          properties=props,
                          env=env)
        )

        if groupId == SDEVEL_GROUP_ID:
            if settings.branchsDict[groupId].get(settings.XMIPP_DOCS_BUILD_ID,
                                                 None) is not None:
                builders.append(
                    BuilderConfig(name="%s%s" % (settings.XMIPP_DOCS_PREFIX, groupId),
                                  tags=["xmippDocs", groupId],
                                  workernames=[settings.WORKER1],
                                  factory=docsFactory(groupId),
                                  workerbuilddir=groupId,
                                  properties={
                                      'slackChannel': "buildbot"},
                                  env=env))



            bundleEnv.update(env)
            builders.append(
                BuilderConfig(name=XMIPP_BUNDLE_TESTS + groupId,
                              tags=[groupId],
                              workernames=[WORKER1],
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
        xmippSchedulerNames.append(XMIPP_DOCS_PREFIX + groupId)
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
