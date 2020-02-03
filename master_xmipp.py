import re

from buildbot.plugins import util, steps
from buildbot.steps.shell import ShellCommand, SetProperty
from buildbot.config import BuilderConfig
from buildbot.schedulers import triggerable
from buildbot.schedulers.forcesched import ForceScheduler

import settings
from settings import (XMIPP_REPO_URL, XMIPP_BUILD_ID, SCIPION_BUILD_ID,
                      XMIPP_INSTALL_PREFIX, timeOutInstall, WORKER,
                      XMIPP_SLACK_CHANNEL,
                      XMIPP_TESTS, XMIPP_BUNDLE_TESTS, NVCC_LINKFLAGS,
                      NVCC_CXXFLAGS,
                      NVCC, CUDA, EMAN212, FORCE_BUILDER_PREFIX, branchsDict,
                      PROD_GROUP_ID,
                      XMIPP_BUNDLE_VARS, DEVEL_GROUP_ID, LD_LIBRARY_PATH,
                      timeOutShort, SDEVEL_GROUP_ID)
from common_utils import changeConfVar, GenerateStagesCommand
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
#                         INSTALL XMIPP FACTORY
# *****************************************************************************
def installXmippFactory(groupId):
    installXmippSteps = util.BuildFactory()
    installXmippSteps.workdir = XMIPP_BUILD_ID
    installXmippSteps.addStep(
        ShellCommand(command=['find', '.', '-mindepth', '1', '-delete'],
                     name='Remove Xmipp directory',
                     description='Delete existing Xmipp dir content',
                     descriptionDone='Remove Xmipp'))
    installXmippSteps.addStep(
        ShellCommand(command=['echo', 'SCIPION_HOME: ',
                              util.Property('SCIPION_HOME')],
                     name='Echo scipion home',
                     description='Echo scipion home',
                     descriptionDone='Echo scipion home',
                     timeout=timeOutShort))
    installXmippSteps.addStep(
        ShellCommand(command=['git', 'clone'] + XMIPP_REPO_URL.split() + ['.'],
                     name='Clone Xmipp repository',
                     description='Getting Xmipp repository',
                     descriptionDone='Xmipp repo downloaded',
                     timeout=timeOutShort,
                     haltOnFailure=True))
    # installXmippSteps.addStep(
    #     ShellCommand(command=['chmod', 'a+x', 'xmipp'],
    #                  name='Make Xmipp script executable',
    #                  description='Making Xmipp script executable',
    #                  descriptionDone='Xmipp script made executable',
    #                  timeout=timeOutShort))

    xmippBranch = branchsDict[groupId].get(XMIPP_BUILD_ID, "")

    if groupId != SDEVEL_GROUP_ID:

        installXmippSteps.addStep(
            ShellCommand(command=['./xmipp', 'get_devel_sources', xmippBranch],
                         name='Get Xmipp devel sources',
                         description='Get Xmipp devel sources',
                         descriptionDone='Get Xmipp devel sources',
                         timeout=timeOutShort)
        )
        installXmippSteps.addStep(
            ShellCommand(command=['./xmipp', 'config'],
                         name='./xmipp config',
                         description='Generate xmipp config',
                         descriptionDone='Generate xmipp config',
                         timeout=timeOutShort)
        )
        installXmippSteps.addStep(
            ShellCommand(command=changeConfVar('CUDA', CUDA, file='xmipp.conf'),
                         name='Set CUDA = True',
                         description='Set CUDA = True',
                         descriptionDone='Set CUDA = True',
                         timeout=timeOutShort)
        )
        installXmippSteps.addStep(
            ShellCommand(command=changeConfVar('NVCC', NVCC, file='xmipp.conf'),
                         name='Set NVCC',
                         description='Set NVCC',
                         descriptionDone='Set NVCC',
                         timeout=timeOutShort)
        )
        installXmippSteps.addStep(
            ShellCommand(command=changeConfVar('NVCC_CXXFLAGS', NVCC_CXXFLAGS, file='xmipp.conf'),
                         name='Set NVCC_CXXFLAGS',
                         description='Set NVCC_CXXFLAGS',
                         descriptionDone='Set NVCC_CXXFLAGS',
                         timeout=timeOutShort)
        )
        installXmippSteps.addStep(
            ShellCommand(command=changeConfVar('NVCC_LINKFLAGS', NVCC_LINKFLAGS, file='xmipp.conf', escapeSlash=True),
                         name='Set NVCC_LINKFLAGS',
                         description='Set NVCC_LINKFLAGS',
                         descriptionDone='Set NVCC_LINKFLAGS',
                         timeout=timeOutShort)
        )
        installXmippSteps.addStep(
            ShellCommand(command=['./xmipp', 'get_dependencies', xmippBranch],
                         name='./xmipp get_dependencies',
                         description='Get Xmipp dependencies',
                         descriptionDone='Get Xmipp dependencies',
                         timeout=timeOutShort)
        )
        installXmippSteps.addStep(
            ShellCommand(command=['./xmipp', 'compile', '8'],
                         name='./xmipp compile',
                         description='Compile Xmipp',
                         descriptionDone='Compiled Xmipp',
                         timeout=timeOutInstall)
        )
        installXmippSteps.addStep(
            ShellCommand(command=['./xmipp', 'install'],
                         name='./xmipp install',
                         description='Install Xmipp',
                         descriptionDone='Installed Xmipp',
                         timeout=timeOutShort)
        )

        installXmippSteps.addStep(
            steps.SetPropertyFromCommand(command='echo $PWD', property='XMIPP_HOME'))

        # linkToSitePkgs = ['ln', '-fs', util.Interpolate('%(prop:XMIPP_HOME)s/src/scipion-em-xmipp/xmipp3'),
        #                   util.Interpolate('%(prop:SCIPION_HOME)s/software/lib/python2.7/site-packages/')]
        #
        # installXmippSteps.addStep(
        #     ShellCommand(command=linkToSitePkgs,
        #                  name='Link Xmipp on site-packages',
        #                  description='Make a link to xmipp on Scipions site-packages',
        #                  descriptionDone='Xmipp linked to site packages',
        #                  timeout=timeOutShort))

        installXmippSteps.addStep(
            ShellCommand(command=['./scipion', 'installp', '-p', util.Interpolate('%(prop:XMIPP_HOME)s/src/scipion-em-xmipp'), '--devel'],
                         name='Install scipion-em-xmipp in devel mode',
                         description='Install scipion-em-xmipp in devel mode',
                         descriptionDone='scipion-em-xmipp in devel mode',
                         timeout=timeOutInstall,
                         haltOnFailure=True,
                         workdir=SCIPION_BUILD_ID)
        )

        linkToSoftwareEm = ['ln', '-fs', util.Interpolate("%(prop:XMIPP_HOME)s/build"),
                            util.Interpolate('%(prop:SCIPION_HOME)s/software/em/xmipp')]
        installXmippSteps.addStep(
            ShellCommand(command=linkToSoftwareEm,
                         name='Link Xmipp build on software/em',
                         description='Make a link to xmipp/build on software/em',
                         descriptionDone='Xmipp build linked to Scipion',
                         timeout=timeOutShort)
        )

        installXmippSteps.addStep(
            ShellCommand(command=['./scipion', 'installb', 'nma'],
                         name='Install NMA',
                         description='Install NMA',
                         descriptionDone='Installed NMA',
                         timeout=timeOutInstall,
                         haltOnFailure=True,
                         workdir=SCIPION_BUILD_ID)
        )

        installXmippSteps.addStep(
            ShellCommand(command=['./scipion', 'installb', 'deepLearningToolkit'],
                         name='Install deepLearningToolkit',
                         description='Install deepLearningToolkit',
                         descriptionDone='Installed deepLearningToolkit',
                         timeout=timeOutInstall,
                         haltOnFailure=True,
                         workdir=SCIPION_BUILD_ID)
        )

        installXmippSteps.addStep(
            ShellCommand(command=['./scipion', 'python', '-m', 'pip', 'install',
                                  'scikit-learn==0.19.1'],
                         name='Install scikit-learn',
                         description='Install scikit-learn',
                         descriptionDone='Installed scikit-learn',
                         timeout=timeOutInstall,
                         haltOnFailure=True,
                         workdir=SCIPION_BUILD_ID)
        )
    else:

        installXmippSteps.addStep(
            ScipionCommandStep(command='./xmipp get_devel_sources %s' % (xmippBranch),
                         name='Get Xmipp devel sources',
                         description='Get Xmipp devel sources',
                         descriptionDone='Get Xmipp devel sources',
                         timeout=timeOutShort)
        )
        installXmippSteps.addStep(
            ScipionCommandStep(command='./xmipp config',
                         name='./xmipp config',
                         description='Generate xmipp config',
                         descriptionDone='Generate xmipp config',
                         timeout=timeOutShort)
        )
        installXmippSteps.addStep(
            ShellCommand(command=changeConfVar('CUDA', CUDA, file='xmipp.conf'),
                         name='Set CUDA = True',
                         description='Set CUDA = True',
                         descriptionDone='Set CUDA = True',
                         timeout=timeOutShort)
        )
        installXmippSteps.addStep(
            ShellCommand(command=changeConfVar('NVCC', NVCC, file='xmipp.conf'),
                         name='Set NVCC',
                         description='Set NVCC',
                         descriptionDone='Set NVCC',
                         timeout=timeOutShort)
        )
        installXmippSteps.addStep(
            ShellCommand(command=changeConfVar('NVCC_CXXFLAGS', NVCC_CXXFLAGS,
                                               file='xmipp.conf'),
                         name='Set NVCC_CXXFLAGS',
                         description='Set NVCC_CXXFLAGS',
                         descriptionDone='Set NVCC_CXXFLAGS',
                         timeout=timeOutShort)
        )
        installXmippSteps.addStep(
            ShellCommand(command=changeConfVar('NVCC_LINKFLAGS', NVCC_LINKFLAGS,
                                               file='xmipp.conf',
                                               escapeSlash=True),
                         name='Set NVCC_LINKFLAGS',
                         description='Set NVCC_LINKFLAGS',
                         descriptionDone='Set NVCC_LINKFLAGS',
                         timeout=timeOutShort)
        )
        installXmippSteps.addStep(
            ScipionCommandStep(command='./xmipp get_dependencies %s' % (xmippBranch),
                         name='./xmipp get_dependencies',
                         description='Get Xmipp dependencies',
                         descriptionDone='Get Xmipp dependencies',
                         timeout=timeOutShort)
        )
        installXmippSteps.addStep(
            ScipionCommandStep(command='./xmipp compile 8',
                         name='./xmipp compile',
                         description='Compile Xmipp',
                         descriptionDone='Compiled Xmipp',
                         timeout=timeOutInstall)
        )
        installXmippSteps.addStep(ScipionCommandStep(command='./xmipp install',
                         name='./xmipp install',
                         description='Install Xmipp',
                         descriptionDone='Installed Xmipp',
                         timeout=timeOutShort))

        installXmippSteps.addStep(
            steps.SetPropertyFromCommand(command='echo $PWD',
                                         property='XMIPP_HOME'))

        linkToSoftwareEm = ['ln', '-fs',
                            util.Interpolate("%(prop:XMIPP_HOME)s/build"),
                            util.Interpolate(
                                '%(prop:SCIPION_HOME)s/software/em/xmipp')]
        installXmippSteps.addStep(
            ShellCommand(command=linkToSoftwareEm,
                         name='Link Xmipp build on software/em',
                         description='Make a link to xmipp/build on software/em',
                         descriptionDone='Xmipp build linked to Scipion',
                         timeout=timeOutShort)
        )

        # Install xmipp plugin
        installXmippPluginCmd = (settings.SCIPION_CMD + ' installp -p ' +
                                 settings.SDEVEL_XMIPP_HOME +
                                 '/src/scipion-em-xmipp --devel')

        installXmippSteps.addStep(
            ScipionCommandStep(command=installXmippPluginCmd,
                         name='Install scipion-em-xmipp in devel mode',
                         description='Install scipion-em-xmipp in devel mode',
                         descriptionDone='scipion-em-xmipp in devel mode',
                         timeout=timeOutInstall,
                         haltOnFailure=True,
                         workdir=SCIPION_BUILD_ID)
        )


        # installDeepLearning = (settings.SCIPION_CMD + ' installb deepLearningToolkit')
        # installXmippSteps.addStep(
        #     ScipionCommandStep(
        #         command=installDeepLearning,
        #         name='Install deepLearningToolkit',
        #         description='Install deepLearningToolkit',
        #         descriptionDone='Installed deepLearningToolkit',
        #         timeout=timeOutInstall,
        #         haltOnFailure=True,
        #         workdir=SCIPION_BUILD_ID)
        # )

        # installXmippSteps.addStep(
        #     ScipionCommandStep(
        #         command='python -m pip install scikit-learn==0.19.1',
        #         name='Install scikit-learn',
        #         description='Install scikit-learn',
        #         descriptionDone='Installed scikit-learn',
        #         timeout=timeOutInstall,
        #         haltOnFailure=True,
        #         workdir=SCIPION_BUILD_ID)
        # )

    return installXmippSteps


# *****************************************************************************
#                         XMIPP BUNDLE FACTORY
# *****************************************************************************
def xmippBundleFactory(groupId):
    xmippTestSteps = util.BuildFactory()
    xmippTestSteps.workdir = XMIPP_BUILD_ID
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
                                  env=util.Property('env')))

        xmippTestSteps.addStep(
            GenerateStagesCommand(command=["./xmipp", "test", "--show"],
                                  name="Generate test stages for Xmipp functions",
                                  description="Generating test stages for Xmipp functions",
                                  descriptionDone="Generate test stages for Xmipp functions",
                                  haltOnFailure=False,
                                  pattern='xmipp_test_(.*)',
                                  env=util.Property('env')))
    else:
        xmippTestSteps.addStep(SetProperty(
            command=["bash", "-c", settings.SCIPION_ENV_ACTIVATION + " ; " + "source build/xmipp.bashrc; env"],
            extract_fn=glob2list,
            env={"SCIPION_HOME": util.Property("SCIPION_HOME"),
                 "SCIPION_LOCAL_CONFIG": util.Property("SCIPION_LOCAL_CONFIG"),
                 "LD_LIBRARY_PATH": LD_LIBRARY_PATH}))

        xmippTestShowcmd = ["bash", "-c", settings.SCIPION_ENV_ACTIVATION +
                            " ; " + "./xmipp test --show"]
        xmippTestSteps.addStep(
            GenerateStagesCommand(command=xmippTestShowcmd,
                                  name="Generate test stages for Xmipp programs",
                                  description="Generating test stages for Xmipp programs",
                                  descriptionDone="Generate test stages for Xmipp programs",
                                  haltOnFailure=False,
                                  pattern='./xmipp test (.*)',
                                  env=util.Property('env')))

        # xmippTestSteps.addStep(
        #     GenerateStagesCommand(command=xmippTestShowcmd,
        #                           name="Generate test stages for Xmipp functions",
        #                           description="Generating test stages for Xmipp functions",
        #                           descriptionDone="Generate test stages for Xmipp functions",
        #                           haltOnFailure=False,
        #                           pattern='xmipp_test_(.*)',
        #                           env=util.Property('env')))

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
        xmippTestSteps.addStep(
            GenerateStagesCommand(command=["./scipion", "test", "--show", "--grep", "xmipp3", "--mode", "onlyclasses"],
                                  name="Generate Scipion test stages for Xmipp",
                                  description="Generating Scipion test stages for Xmipp",
                                  descriptionDone="Generate Scipion test stages for Xmipp",
                                  haltOnFailure=False,
                                  stagePrefix=["./scipion", "test"],
                                  targetTestSet='xmipp3',
                                  stageEnvs=envs))

    else:

        xmippTestShowcmd = ["bash", "-c", settings.SCIPION_ENV_ACTIVATION +
                            " ; " + "python -m scipion test --show --grep xmipp3 --mode onlyclasses"]

        xmippTestSteps.addStep(
            GenerateStagesCommand(
                command=xmippTestShowcmd,
                name="Generate Scipion test stages for Xmipp",
                description="Generating Scipion test stages for Xmipp",
                descriptionDone="Generate Scipion test stages for Xmipp",
                haltOnFailure=False,
                stagePrefix=[settings.SCIPION_CMD, "test"],
                targetTestSet='xmipp3',
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

    if groupId != SDEVEL_GROUP_ID:

        if groupId == PROD_GROUP_ID:
            builders.append(
                BuilderConfig(name=XMIPP_INSTALL_PREFIX + groupId,
                              workernames=[WORKER],
                              tags=[groupId],
                              factory=pluginFactory(groupId, 'scipion-em-xmipp', shortname='xmipp3', doTest=False,
                                                    extraBinaries=['xmippSrc', 'deepLearningToolkit', 'nma']),
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

        else:
            builders.append(
                BuilderConfig(name=XMIPP_INSTALL_PREFIX + groupId,
                              workernames=[WORKER],
                              tags=[groupId],
                              factory=installXmippFactory(groupId),
                              workerbuilddir=groupId,
                              env=installEnv,
                              properties=props)
            )

            builders.append(
                BuilderConfig(name=XMIPP_TESTS + groupId,
                              tags=[groupId],
                              workernames=[WORKER],
                              factory=xmippTestFactory(groupId),
                              workerbuilddir=groupId,
                              properties=props,
                              env=env)
            )

            builders.append(
                BuilderConfig(name=XMIPP_BUNDLE_TESTS + groupId,
                              tags=[groupId],
                              workernames=[WORKER],
                              factory=xmippBundleFactory(groupId),
                              workerbuilddir=groupId,
                              env=bundleEnv,
                              properties=props)
            )

    else:
        builders.append(
            BuilderConfig(name=XMIPP_INSTALL_PREFIX + groupId,
                          workernames=[WORKER],
                          tags=[groupId],
                          factory=installXmippFactory(groupId),
                          workerbuilddir=groupId,
                          env=installEnv,
                          properties=props)
        )
        env = {
            "SCIPION_IGNORE_PYTHONPATH": "True",
            "SCIPION_LOCAL_CONFIG": util.Property("SCIPION_LOCAL_CONFIG"),
            "SCIPION_HOME": util.Property('SCIPION_HOME')
        }
        builders.append(
            BuilderConfig(name=XMIPP_TESTS + groupId,
                          tags=[groupId],
                          workernames=[WORKER],
                          factory=xmippTestFactory(groupId),
                          workerbuilddir=groupId,
                          properties=props,
                          env=env)
        )

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

    xmippSchedulerNames = [XMIPP_TESTS + groupId, XMIPP_INSTALL_PREFIX + groupId]

    if groupId == DEVEL_GROUP_ID or groupId == SDEVEL_GROUP_ID:
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
