import re

from buildbot.plugins import util, steps
from buildbot.steps.shell import ShellCommand, SetPropertyFromCommand
from buildbot.config import BuilderConfig
from buildbot.schedulers import triggerable
from buildbot.schedulers.forcesched import ForceScheduler

from settings import (XMIPP_SCRIPT_URL, XMIPP_BUILD_ID, SCIPION_BUILD_ID, XMIPP_INSTALL_PREFIX,
                      XMIPP_TESTS, XMIPP_BUNDLE_TESTS, NVCC_LINKFLAGS, NVCC_CXXFLAGS, NVCC, CUDA, EMAN212,
                      FORCE_BUILDER_PREFIX, branchsDict, timeOutInstall, WORKER)
from common_utils import changeConfVar, GenerateStagesCommand


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


# *****************************************************************************
#                         INSTALL XMIPP FACTORY
# *****************************************************************************
def installXmippFactory(groupId):
    installXmippSteps = util.BuildFactory()
    installXmippSteps.workdir = XMIPP_BUILD_ID
    installXmippSteps.addStep(
        ShellCommand(command=['echo', 'SCIPION_HOME: ',
                              util.Property('SCIPION_HOME')],
                     name='Echo scipion home',
                     description='Echo scipion home',
                     descriptionDone='Echo scipion home',
                     timeout=300))
    installXmippSteps.addStep(
        ShellCommand(command=['wget', XMIPP_SCRIPT_URL, '-O', 'xmipp'],
                     name='Get XMIPP script',
                     description='Getting Xmipp script',
                     descriptionDone='Xmipp script downloaded',
                     timeout=300))
    installXmippSteps.addStep(
        ShellCommand(command=['chmod', 'a+x', 'xmipp'],
                     name='Make Xmipp script executable',
                     description='Making Xmipp script executable',
                     descriptionDone='Xmipp script made executable',
                     timeout=300))

    xmippBranch = branchsDict[groupId].get(XMIPP_BUILD_ID, None)

    installXmippSteps.addStep(
        ShellCommand(command=['./xmipp', 'get_devel_sources', xmippBranch],
                     name='Get Xmipp devel sources',
                     description='Get Xmipp devel sources',
                     descriptionDone='Get Xmipp devel sources',
                     timeout=300))

    installXmippSteps.addStep(
        ShellCommand(command=['./xmipp', 'config'],
                     name='Generate xmipp config',
                     description='Generate xmipp config',
                     descriptionDone='Generate xmipp config',
                     timeout=300)
    )

    installXmippSteps.addStep(
        ShellCommand(command=changeConfVar('CUDA', CUDA, 'xmipp.conf'),
                     name='Set CUDA = True',
                     description='Set CUDA = True',
                     descriptionDone='Set CUDA = True',
                     timeout=300)
    )
    installXmippSteps.addStep(
        ShellCommand(command=changeConfVar('NVCC', NVCC, 'xmipp.conf'),
                     name='Set NVCC',
                     description='Set NVCC',
                     descriptionDone='Set NVCC',
                     timeout=300)
    )
    nvcc_cxxflags = '--x cu -D_FORCE_INLINES -Xcompiler -fPIC -Wno-deprecated-gpu-targets -ccbin g++-5'
    installXmippSteps.addStep(
        ShellCommand(command=changeConfVar('NVCC_CXXFLAGS', NVCC_CXXFLAGS, 'xmipp.conf'),
                     name='Set NVCC_CXXFLAGS',
                     description='Set NVCC_CXXFLAGS',
                     descriptionDone='Set NVCC_CXXFLAGS',
                     timeout=300)
    )
    installXmippSteps.addStep(
        ShellCommand(command=changeConfVar('NVCC_LINKFLAGS', NVCC_LINKFLAGS, 'xmipp.conf'),
                     name='Set NVCC_LINKFLAGS',
                     description='Set NVCC_LINKFLAGS',
                     descriptionDone='Set NVCC_LINKFLAGS',
                     timeout=300)
    )
    installXmippSteps.addStep(
        ShellCommand(command=['./xmipp', 'compile', '8'],
                     name='Compile Xmipp',
                     description='Compile Xmipp',
                     descriptionDone='Compiled Xmipp',
                     timeout=300)
    )
    installXmippSteps.addStep(
        ShellCommand(command=['./xmipp', 'install'],
                     name='Compile Xmipp',
                     description='Compile Xmipp',
                     descriptionDone='Compiled Xmipp',
                     timeout=300)
    )

    installXmippSteps.addStep(
        steps.SetPropertyFromCommand(command='echo $PWD', property='XMIPP_HOME'))

    linkToSitePkgs = ['ln', '-fs', util.Interpolate('%(prop:XMIPP_HOME)s/src/scipion-em-xmipp/xmipp3'),
                      util.Interpolate('%(prop:SCIPION_HOME)s/software/lib/python2.7/site-packages/')]

    installXmippSteps.addStep(
        ShellCommand(command=linkToSitePkgs,
                     name='Link Xmipp on site-packages',
                     description='Make a link to xmipp on Scipions site-packages',
                     descriptionDone='Xmipp linked to site packages',
                     timeout=300))

    linkToSoftwareEm = ['ln', '-fs', util.Interpolate("%(prop:XMIPP_HOME)s/build"),
                        util.Interpolate('%(prop:SCIPION_HOME)s/software/em/xmipp')]
    installXmippSteps.addStep(
        ShellCommand(command=linkToSoftwareEm,
                     name='Link Xmipp build on software/em',
                     description='Make a link to xmipp/build on software/em',
                     descriptionDone='Xmipp build linked to Scipion',
                     timeout=300)
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

    return installXmippSteps


# *****************************************************************************
#                         XMIPP BUNDLE FACTORY
# *****************************************************************************
def xmippBundleFactory():
    xmippTestSteps = util.BuildFactory()
    xmippTestSteps.workdir = XMIPP_BUILD_ID
    xmippTestSteps.addStep(
        SetPropertyFromCommand(command='cat build/xmipp.bashrc',
                               extract_fn=xmippBashrc2Dict,
                               name='Get vars from xmipp.bashrc',
                               description='Get vars from xmipp.bashrc',
                               descriptionDone='Get vars from xmipp.bashrc',
                               timeout=60))

    xmippTestSteps.addStep(
        GenerateStagesCommand(command=["./xmipp", "test", "--show"],
                              name="Generate test stages for Xmipp",
                              description="Generating test stages for Xmipp",
                              descriptionDone="Generate test stages for Xmipp",
                              haltOnFailure=False,
                              pattern='./xmipp test (.*)',
                              stagePrefix=['./xmipp', 'test']))

    xmippTestSteps.addStep(
        GenerateStagesCommand(command=["./xmipp", "test", "--show"],
                              name="Generate test stages for Xmipp",
                              description="Generating test stages for Xmipp",
                              descriptionDone="Generate test stages for Xmipp",
                              haltOnFailure=False,
                              pattern='xmipp_test_(.*)',
                              stagePrefix=[]))

    return xmippTestSteps


# *****************************************************************************
#                         XMIPP TEST FACTORY IN SCIPION
# *****************************************************************************
def xmippTestFactory():
    xmippTestSteps = util.BuildFactory()
    xmippTestSteps.workdir = util.Property('SCIPION_HOME')
    xmippTestSteps.addStep(ShellCommand(command=['echo', 'SCIPION_HOME: ', util.Property('SCIPION_HOME')],
                                        name='Echo scipion home',
                                        description='Echo scipion home',
                                        descriptionDone='Echo scipion home',
                                        timeout=300
                                        ))
    # add TestRelionExtractStreaming manually because it needs eman 2.12
    gpucorrclassifiers = ["xmipp3.tests.test_protocols_gpuCorr_classifier.TestGpuCorrClassifier",
                          "xmipp3.tests.test_protocols_gpuCorr_semiStreaming.TestGpuCorrSemiStreaming",
                          "xmipp3.tests.test_protocols_gpuCorr_fullStreaming.TestGpuCorrFullStreaming"]

    envs = {gpucorrcls: EMAN212 for gpucorrcls in gpucorrclassifiers}

    xmippTestSteps.addStep(
        GenerateStagesCommand(command=["./scipion", "test", "--show", "--grep", "xmipp3", "--mode", "onlyclasses"],
                              name="Generate Scipion test stages for Xmipp",
                              description="Generating Scipion test stages for Xmipp",
                              descriptionDone="Generate Scipion test stages for Xmipp",
                              haltOnFailure=False,
                              targetTestSet='xmipp3',
                              envs=envs))

    return xmippTestSteps


# #############################################################################
# ############################## BUILDERS #####################################
# #############################################################################

def getXmippBuilders(groupId):
    builders = []
    builders.append(
        BuilderConfig(name=XMIPP_INSTALL_PREFIX + groupId,
                      workernames=[WORKER],
                      tags=[groupId],
                      factory=installXmippFactory(groupId),
                      workerbuilddir=groupId,
                      env={'SCIPION_HOME': util.Property('SCIPION_HOME'),
                           "SCIPION_IGNORE_PYTHONPATH": "True",
                           'PATH': ["/usr/local/cuda/bin",
                                    "${PATH}"]
                           },
                      properties={'slackChannel': "xmipp"})
    )

    builders.append(
        BuilderConfig(name=XMIPP_BUNDLE_TESTS + groupId,
                      tags=[groupId],
                      workernames=[WORKER],
                      factory=xmippBundleFactory(),
                      workerbuilddir=groupId,
                      env={"SCIPION_IGNORE_PYTHONPATH": "True",
                           'PATH': ["/usr/local/cuda/bin",
                                    "${PATH}"]
                           },
                      properties={'slackChannel': "xmipp"})
    )

    builders.append(
        BuilderConfig(name=XMIPP_TESTS + groupId,
                      tags=[groupId],
                      workernames=[WORKER],
                      factory=xmippTestFactory(),
                      workerbuilddir=groupId,
                      properties={'slackChannel': "xmipp"},
                      env={"SCIPION_IGNORE_PYTHONPATH": "True"})
    )

    return builders


# #############################################################################
# ############################## SCHEDULERS ###################################
# #############################################################################

def getXmippSchedulers(groupId):
    xmippSchedulerNames = [XMIPP_INSTALL_PREFIX + groupId,
                           XMIPP_BUNDLE_TESTS + groupId,
                           XMIPP_TESTS + groupId]
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
