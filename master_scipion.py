import json
from collections import OrderedDict

from buildbot.steps.shell import ShellCommand, SetPropertyFromCommand
from buildbot.plugins import util, steps
from buildbot.steps.source.git import Git
from buildbot.config import BuilderConfig
from buildbot.schedulers import triggerable
from buildbot.schedulers.forcesched import ForceScheduler

import settings
from common_utils import changeConfVar, GenerateStagesCommand

# #############################################################################
# ########################## COMMANDS & UTILS #################################
# #############################################################################

with open(settings.PLUGINS_JSON_FILE) as f:
    # read in order, since we have taken into account dependencies in
    # between plugins when completing the json file
    scipionPlugins = json.load(f, object_pairs_hook=OrderedDict)
    xmippPluginData = scipionPlugins.pop('scipion-em-xmipp')
    locscalePluginData = scipionPlugins.pop("scipion-em-locscale")

# Remove config/scipion.conf
removeScipionConf = ShellCommand(
    command=['rm', '-f', 'config/scipion.conf'],
    name='Clean Scipion Config',
    description='Delete existing conf file at scipion HOME',
    descriptionDone='Remove config/scipion.conf',
    haltOnFailure=False)

# Remove HOME/.config/scipion/scipion.conf
removeHomeConfig = ShellCommand(command=['bash', '-c',
                                         util.Interpolate("rm %(prop:SCIPION_LOCAL_CONFIG)s")],
                                name='Clean Scipion Config at USERS HOME',
                                description='Delete existing conf file at users HOME',
                                descriptionDone='Remove USER HOME scipion.conf',
                                haltOnFailure=False)

# Regenerate the scipion.config files
configScipion = ShellCommand(
    command=['./scipion', 'config', '--notify', '--overwrite'],
    name='Scipion Config',
    description='Create installation configuration files',
    descriptionDone='Scipion config',
    haltOnFailure=True)

# Avoid notifications from BuildBot
setNotifyAtFalse = ShellCommand(
    command=['bash', '-c', util.Interpolate('sed -i -e '
                                            '"s/MPI_LIBDIR = True/'
                                            'SCIPION_NOTIFY = False/g" %(prop:SCIPION_LOCAL_CONFIG)s')],
    name='Cancel notifications',
    description='Do not notify usage. Server will be out of '
                'the blacklist in order for the notify test to work',
    descriptionDone='Disable notification',
    haltOnFailure=True)

setGeneralCuda = ShellCommand(
    command=changeConfVar("CUDA", settings.CUDA),
    name='Set CUDA equals True',
    description='Set CUDA equals True',
    descriptionDone='Set CUDA equals True',
    haltOnFailure=True)

setMpiLibPath = ShellCommand(
    # command=changeConfVar.withArgs('MPI_LIBDIR', mpilibdir),
    command=changeConfVar("MPI_LIBDIR", settings.MPI_LIBDIR, escapeSlash=True),
    name='Change MPI_LIBDIR',
    description='Add the right MPI_LIBDIR path',
    descriptionDone='Added MPI_LIBDIR',
    haltOnFailure=True)

setMpiIncludePath = ShellCommand(
    command=changeConfVar('MPI_INCLUDE', settings.MPI_INCLUDE, escapeSlash=True),
    name='Change MPI_INCLUDE',
    description='Add the right MPI_INCLUDE path',
    descriptionDone='Added MPI_INCLUDE',
    haltOnFailure=True)

setMpiBinPath = ShellCommand(
    command=changeConfVar('MPI_BINDIR', settings.MPI_BINDIR, escapeSlash=True),
    name='Change MPI_BINDIR',
    description='Add the right MPI_BINDIR path',
    descriptionDone='Added MPI_BINDIR',
    haltOnFailure=True)

# Use a common home data tests folder to save storage
setDataTestsDir = ShellCommand(
    command=['sed', '-i', '-e',
             's/SCIPION_TESTS = data\/tests/'
             'SCIPION_TESTS = ~\/data\/tests/g',
             'config/scipion.conf'],
    name='Set data tests dir',
    description='Using a common data tests dir',
    descriptionDone='Change data tests dir',
    haltOnFailure=True)


# Use an internal dir to allow a branch-dependent project inspection
@util.renderer
def renderScipionUserDataCmd(props):
    command = ['bash', '-c']
    userDataHome = props.getProperty('BUILD_GROUP_HOME')
    userConfig = props.getProperty('SCIPION_LOCAL_CONFIG')
    if userDataHome:
        command.append('sed -i -e '
                       '"s/SCIPION_USER_DATA = ~\/ScipionUserData/'
                       'SCIPION_USER_DATA = %s\/ScipionUserData/g" '
                       '%s' % (userDataHome.replace('/', '\/'), userConfig))

    return command


setScipionUserData = ShellCommand(
    command=renderScipionUserDataCmd,
    name='Set ScipionUserData dir',
    description='Using an independent ScipionUserData dir.',
    descriptionDone='Change ScipionUserData dir',
    haltOnFailure=True)

setMotioncorrCuda = ShellCommand(
    command=util.Interpolate(
        'sed -ie "\$aMOTIONCORR_CUDA_LIB = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.CUDA_LIB)),
    name='Set MOTIONCORR_CUDA_LIB in scipion conf',
    description='Set MOTIONCORR_CUDA_LIB in scipion conf',
    descriptionDone='Set MOTIONCORR_CUDA_LIB in scipion conf',
    haltOnFailure=True)

setCcp4Home = ShellCommand(
    command=util.Interpolate('sed -ie "\$aCCP4_HOME = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.CCP4_HOME)),
    name='Set CCP4_HOME in scipion conf',
    description='Set CCP4_HOME in scipion conf',
    descriptionDone='Set CCP4_HOME in scipion conf',
    haltOnFailure=True)

setCryoloModel = ShellCommand(
    command=util.Interpolate('sed -ie "\$aCRYOLO_GENERIC_MODEL = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.CRYOLO_GENERIC_MODEL)),
    name='Set CRYOLO_GENERIC_MODEL in scipion conf',
    description='Set CRYOLO_GENERIC_MODEL in scipion conf',
    descriptionDone='Set CRYOLO_GENERIC_MODEL in scipion conf',
    haltOnFailure=True)

setCryoloEnvActivation = ShellCommand(
    command=util.Interpolate('sed -ie "\$aCRYOLO_ENV_ACTIVATION = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.CRYOLO_ENV_ACTIVATION)),
    name='Set CRYOLO_ENV_ACTIVATION in scipion conf',
    description='Set CRYOLO_ENV_ACTIVATION in scipion conf',
    descriptionDone='Set CRYOLO_ENV_ACTIVATION in scipion conf',
    haltOnFailure=True)

setScipionEnvActivation = ShellCommand(
    command=util.Interpolate('sed -ie "\$aSCIPION_ENV_ACTIVATION = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.SCIPION_ENV_ACTIVATION)),
    name='Set SCIPION_ENV_ACTIVATION in scipion conf',
    description='Set SCIPION_ENV_ACTIVATION in scipion conf',
    descriptionDone='Set SCIPION_ENV_ACTIVATION in scipion conf',
    haltOnFailure=True)


setPhenixHome = ShellCommand(
    command=util.Interpolate(
        'sed -ie "\$aPHENIX_HOME = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.PHENIX_HOME)),
    name='Set PHENIX_HOME in scipion conf',
    description='Set PHENIX_HOME in scipion conf',
    descriptionDone='Set PHENIX_HOME in scipion conf',
    haltOnFailure=True)


setCryosparcHome = ShellCommand(
    command=util.Interpolate(
        'sed -ie "\$aCRYOSPARC_DIR = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.CRYOSPARC_DIR)),
    name='Set CRYOSPARC_DIR in scipion conf',
    description='Set CRYOSPARC_DIR in scipion conf',
    descriptionDone='Set CRYOSPARC_DIR in scipion conf',
    haltOnFailure=True)

setCryosparcUser = ShellCommand(
    command=util.Interpolate(
        'sed -ie "\$aCRYOSPARC_USER = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.CRYOSPARC_USER)),
    name='Set CRYOSPARC_USER in scipion conf',
    description='Set CRYOSPARC_USER in scipion conf',
    descriptionDone='Set CRYOSPARC_USER in scipion conf',
    haltOnFailure=True)


installEman212 = ShellCommand(command=['./scipion', 'installb', 'eman-2.12'],
                              name='Install eman-2.12',
                              description='Install eman-2.12',
                              descriptionDone='Installed eman-2.12',
                              timeout=settings.timeOutInstall,
                              haltOnFailure=True)

setCondaActivation = ShellCommand(
    command=util.Interpolate('sed -ie "\$aCONDA_ACTIVATION_CMD = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.CONDA_ACTIVATION_CMD)),
    name='Set CONDA_ACTIVATION_CMD in scipion conf',
    description='Set CONDA_ACTIVATION_CMD in scipion conf',
    descriptionDone='CONDA_ACTIVATION_CMD set in scipion conf',
    haltOnFailure=True)


# Command to clean software/EM packages
removeEMPackages = ShellCommand(
    command=['bash', '-c', 'ls software/em/ -1 -I xmipp | '
                           'xargs -i rm -rf "software/em/"{}'],
    name='Clean EM packages',
    description='Delete existing EM sofware packages',
    descriptionDone='Remove EM packages',
    haltOnFailure=False)

# Clean the downloaded packages in order to get an actualized version
removeEMtgz = ShellCommand(
    command=['bash', '-c',
             'rm -rf software/tmp/* ; '
             'rm -rf software/em/*.tgz'],
    name='Clean tgz files',
    description='Delete downloaded tgz files to get the last version',
    descriptionDone='Remove EM tgz',
    haltOnFailure=False)

# Clean the Cryosparc projects
removeCryosParcProjectTest = ShellCommand(
    command=['bash', '-c',
             'rm -rf /home/buildbot/cryosparc/scipion_projects/* ; '],
    name='Clean CryosPARC projects',
    description='Delete CryosPARC projects',
    descriptionDone='Delete CryosPARC projects',
    haltOnFailure=False)


def addScipionGitAndConfigSteps(factorySteps, groupId):
    """ The initial steps are common in all builders.
         1. git pull in a certain branch.
         2. remove scipion.config files.
         3. regenerate scipion.config files
         4. set notify at False
         5. set dataTests folder to a common dir (to save space)
         6. set ScipionUserData to an internal folder (to allow branch-dependent project inspection)
    """
    if groupId != settings.SDEVEL_GROUP_ID:
        factorySteps.addStep(Git(repourl=settings.gitRepoURL,
                                 branch=settings.branchsDict[groupId].get(settings.SCIPION_BUILD_ID, None),
                                 mode='incremental',
                                 name='Scipion Git Repository Pull',
                                 haltOnFailure=True))

    factorySteps.addStep(removeScipionConf)
    factorySteps.addStep(removeHomeConfig)

    if groupId == settings.SDEVEL_GROUP_ID:
        factorySteps.addStep(sdevelConfigScipion)
    else:
        factorySteps.addStep(configScipion)

    factorySteps.addStep(setNotifyAtFalse)
    factorySteps.addStep(setGeneralCuda)
    factorySteps.addStep(setMpiLibPath)
    factorySteps.addStep(setMpiBinPath)
    factorySteps.addStep(setMpiIncludePath)
    factorySteps.addStep(setDataTestsDir)
    # factorySteps.addStep(removeScipionUserData)  # to avoid old tests when are renamed
    factorySteps.addStep(setScipionUserData)

    return factorySteps


def addSDevelScipionGitAndConfigSteps(factorySteps, groupId):
    """ The initial steps to sdevel builders.
         1. Remove scipion-em, scipion-app and scipion-pyworkflow to get the last version
         1. git pull scipion-app, scipion-pyworkflow, scipion-em.
         2. remove scipion.config files.
         3. regenerate scipion.config files
         4. set notify at False
         5. set dataTests folder to a common dir (to save space)
         6. set ScipionUserData to an internal folder (to allow branch-dependent project inspection)
    """
    factorySteps.addStep(removeScipionModules)

    factorySteps.addStep(
        ShellCommand(command=['git', 'clone'] + settings.sdevel_gitRepoURL.split(),
                     name='Clone scipion-app repository',
                     description='Getting scipion-app repository',
                     descriptionDone='scipion-app repo downloaded',
                     timeout=settings.timeOutShort,
                     haltOnFailure=True))

    factorySteps.addStep(
        ShellCommand(command=['git', 'clone'] + settings.sdevel_pw_gitRepoURL.split(),
                     name='Clone scipion-pyworkflow repository',
                     description='Getting scipion-pyworkflow repository',
                     descriptionDone='scipion-pyworkflow repo downloaded',
                     timeout=settings.timeOutShort,
                     haltOnFailure=True))

    factorySteps.addStep(
        ShellCommand(command=['git', 'clone'] + settings.sdevel_pyem_gitRepoURL.split(),
                     name='Clone scipion-em repository',
                     description='Getting scipion-em repository',
                     descriptionDone='scipion-em repo downloaded',
                     timeout=settings.timeOutShort,
                     haltOnFailure=True))

    factorySteps.addStep(removeScipionConf)
    # factorySteps.addStep(removeHomeConfig)

    return factorySteps

# Command to install Scipion and/or recompile Xmipp
installScipion = ShellCommand(command=['./scipion', 'install', '-j', '8'],
                              name='Scipion Install',
                              description='Compiling everything that needs re-compiling',
                              descriptionDone='Install Scipion',
                              timeout=settings.timeOutInstall,
                              haltOnFailure=True)


# Command to activate the Snaconda virtual environment
EnvActivation = ShellCommand(command=settings.CONDA_ACTIVATION_CMD.split(),
                              name='Conda activation command',
                              description='Conda activation command',
                              descriptionDone='Conda activation command',
                              timeout=settings.timeOutInstall,
                              haltOnFailure=True)

# Command to change the virtual environment to install the new version of Scipion
# setScipionEnv = ShellCommand(command=settings.SCIPION_ENV_ACTIVATION.split(),
#                               name='Setting Scipion Environ',
#                               description='Setting Scipion Environ',
#                               descriptionDone='Setting Scipion Environ',
#                               timeout=settings.timeOutInstall,
#                               haltOnFailure=True)

installSdevelScipion = ShellCommand(command=['python', '-m', 'pip', 'install', '-e', '.'],
                              name='Scipion Install',
                              description='Install Scipion-module as devel mode',
                              descriptionDone='Install Scipion',
                              timeout=settings.timeOutInstall,
                              haltOnFailure=True)

moveUpLevel = ShellCommand(
    command=['bash', '-c', 'cd', ' ..'],
    name='Move to parent directory',
    description='Move to parent directory',
    descriptionDone='to parent directory',
    haltOnFailure=False)

moveScipionApp = ShellCommand(
    command=['bash', '-c', 'cd', 'scipion-app'],
    name='Scipion-App directory',
    description='Move to scipion-App directory',
    descriptionDone='Scipion-App directory',
    haltOnFailure=False)

moveScipionEm = ShellCommand(
    command=['bash', '-c', 'cd', 'scipion-em'],
    name='Scipion-App directory',
    description='Move to scipion-App directory',
    descriptionDone='Scipion-App directory',
    haltOnFailure=False)

moveScipionPyworkflow = ShellCommand(
    command=['cd', 'scipion-pyworkflow'],
    name='Scipion-App directory',
    description='Move to scipion-pyworkflow directory',
    descriptionDone='Scipion-App directory',
    haltOnFailure=False)


removeScipionModules = ShellCommand(
    command=['bash', '-c',
             'rm -rf scipion-em ; '
             'rm -rf scipion-pyworkflow ; '
             'rm -rf scipion-app'],
    name='Clean scipion modules',
    description='Delete the scipion modules to get the last versions',
    descriptionDone='Remove EM scipion modules',
    haltOnFailure=False)

sdevelConfigScipion = ShellCommand(
    command=['bash', 'scipion-app/scipion.sh', 'config', '--notify', '--overwrite'],
    name='Scipion Config',
    description='Create installation configuration files',
    descriptionDone='Scipion config',
    haltOnFailure=True)

setScipionEnv = ShellCommand(command=['.', '/home/buildbot/miniconda3/etc/profile.d/conda.sh ; '
                                      'conda activate scipion_python3'],
                              name='Setting Scipion Environ',
                              description='Setting Scipion Environ',
                              descriptionDone='Setting Scipion Environ',
                              timeout=settings.timeOutInstall,
                              haltOnFailure=True)




# #############################################################################
# ############################## FACTORIES ####################################
# #############################################################################

# *****************************************************************************
#                         INSTALL SCIPION FACTORY
# *****************************************************************************
def installScipionFactory(groupId):
    installScipionFactorySteps = util.BuildFactory()
    installScipionFactorySteps.workdir = settings.SCIPION_BUILD_ID
    installScipionFactorySteps = addScipionGitAndConfigSteps(installScipionFactorySteps,
                                                             groupId)
    installScipionFactorySteps.addStep(ShellCommand(command=['echo', 'SCIPION_LOCAL_CONFIG',
                                                             util.Property('SCIPION_LOCAL_CONFIG')],
                                                    name='Echo SCIPION_LOCAL_CONFIG',
                                                    description='Echo SCIPION_LOCAL_CONFIG',
                                                    descriptionDone='Echo SCIPION_LOCAL_CONFIG',
                                                    timeout=settings.timeOutShort
                                                    ))
    installScipionFactorySteps.addStep(installScipion)
    installScipionFactorySteps.addStep(
        ShellCommand(command=['ls', '-1', 'software/lib'],
                     name='Test software/lib',
                     description='Test if software/lib created after installing scipion',
                     descriptionDone='Test scipion installation',
                     haltOnFailure=True))
    installScipionFactorySteps.addStep(
        steps.JSONStringDownload(dict(scipionPlugins, **{"scipion-em-locscale": locscalePluginData}),
                                 workerdest="plugins.json"))
    installScipionFactorySteps.addStep(setMotioncorrCuda)
    installScipionFactorySteps.addStep(setPhenixHome)
    installScipionFactorySteps.addStep(setCryosparcHome)
    installScipionFactorySteps.addStep(setCryosparcUser)
    installScipionFactorySteps.addStep(setCcp4Home)
    installScipionFactorySteps.addStep(setCryoloModel)
    installScipionFactorySteps.addStep(setCryoloEnvActivation)
    installScipionFactorySteps.addStep(setCondaActivation)
    return installScipionFactorySteps


def installSDevelScipionFactory(groupId):
    installScipionFactorySteps = util.BuildFactory()
    installScipionFactorySteps.workdir = settings.SCIPION_BUILD_ID
    installScipionFactorySteps = addSDevelScipionGitAndConfigSteps(installScipionFactorySteps,
                                                             groupId)

    installScipionFactorySteps.addStep(ShellCommand(command=['echo', 'SCIPION_LOCAL_CONFIG',
                                                             util.Property('SCIPION_LOCAL_CONFIG')],
                                                    name='Echo SCIPION_LOCAL_CONFIG',
                                                    description='Echo SCIPION_LOCAL_CONFIG',
                                                    descriptionDone='Echo SCIPION_LOCAL_CONFIG',
                                                    timeout=settings.timeOutShort
                                                    ))
    # Activating the Anaconda environment
    # Set the anaconda environment
    installScipionFactorySteps.addStep(setScipionEnvActivation)
    installScipionFactorySteps.addStep(setScipionEnv)

    # Install scipion-pyworkflow
    installScipionFactorySteps.addStep(moveScipionPyworkflow)
    installScipionFactorySteps.addStep(installSdevelScipion)

    # Install scipion-em
    installScipionFactorySteps.addStep(moveUpLevel)
    installScipionFactorySteps.addStep(moveScipionEm)
    installScipionFactorySteps.addStep(installSdevelScipion)

    # Install scipion-app
    installScipionFactorySteps.addStep(moveUpLevel)
    installScipionFactorySteps.addStep(moveScipionApp)
    installScipionFactorySteps.addStep(sdevelConfigScipion)
    installScipionFactorySteps.addStep(setScipionEnvActivation)
    installScipionFactorySteps.addStep(moveUpLevel)
    # factorySteps.addStep(removeScipionUserData)  # to avoid old tests when are renamed
    installScipionFactorySteps.addStep(setScipionUserData)
    installScipionFactorySteps.addStep(setNotifyAtFalse)
    installScipionFactorySteps.addStep(setGeneralCuda)
    installScipionFactorySteps.addStep(setMpiLibPath)
    installScipionFactorySteps.addStep(setMpiBinPath)
    installScipionFactorySteps.addStep(setMpiIncludePath)
    installScipionFactorySteps.addStep(setDataTestsDir)

    return installScipionFactorySteps


# *****************************************************************************
#                         SCIPION TEST FACTORY
# *****************************************************************************
def scipionTestFactory(groupId):


    scipionTestSteps = util.BuildFactory()
    scipionTestSteps.workdir = util.Property('SCIPION_HOME')

    emanVar = settings.EMAN212 if groupId == settings.PROD_GROUP_ID else settings.EMAN23

    # add TestRelionExtractStreaming manually because it needs eman 2.12
    wfRelionExtractStreaming = 'pyworkflow.tests.em.workflows.test_workflow_streaming.TestRelionExtractStreaming'

    # gen stages
    genStagesCmd = ["./scipion", "test", "--show", "--grep", "pyworkflow", "--mode", "onlyclasses"]
    scipionTestSteps.addStep(
        GenerateStagesCommand(command=genStagesCmd,
                              name="Generate Scipion test stages",
                              description="Generating Scipion test stages",
                              descriptionDone="Generate Scipion test stages",
                              haltOnFailure=False,
                              targetTestSet='pyworkflow',
                              stagePrefix=["./scipion", "test"],
                              blacklist=settings.SCIPION_TESTS_BLACKLIST,
                              stageEnvs={wfRelionExtractStreaming: emanVar}))

    for pwLongTest in settings.SCIPION_LONG_TESTS:  # execute long tests at the end
        if pwLongTest.endswith("TestBPV"):
            scipionTestSteps.addStep(ShellCommand(command=['./scipion', 'test', pwLongTest],
                                                  name=pwLongTest,
                                                  description='Testing %s' % pwLongTest.split('.')[-1],
                                                  descriptionDone=pwLongTest.split('.')[-1],
                                                  timeout=settings.timeOutExecute,
                                                  env=emanVar))
            continue

        scipionTestSteps.addStep(ShellCommand(command=['./scipion', 'test', pwLongTest],
                                              name=pwLongTest,
                                              description='Testing %s' % pwLongTest.split('.')[-1],
                                              descriptionDone=pwLongTest.split('.')[-1],
                                              timeout=settings.timeOutExecute))

    return scipionTestSteps


# *****************************************************************************
#                         PLUGIN FACTORY
# *****************************************************************************
def pluginFactory(pluginName, factorySteps=None, shortname=None,
                  doInstall=True, extraBinaries='', doTest=True):
    factorySteps = factorySteps or util.BuildFactory()
    factorySteps.workdir = util.Property('SCIPION_HOME')
    shortName = shortname or str(pluginName.rsplit('-', 1)[-1])  # todo: get module names more properly?
    if doInstall:
        factorySteps.addStep(ShellCommand(command=['./scipion', 'installp', '-p', pluginName, '-j', '8'],
                                          name='Install plugin %s' % shortName,
                                          description='Install plugin %s' % shortName,
                                          descriptionDone='Installed plugin %s' % shortName,
                                          timeout=settings.timeOutInstall,
                                          haltOnFailure=True))

        factorySteps.addStep(ShellCommand(command=['./scipion', 'python', 'pyworkflow/install/inspect-plugins.py',
                                                   shortName],
                                          name='Inspect plugin %s' % shortName,
                                          description='Inspect plugin %s' % shortName,
                                          descriptionDone='Inspected plugin %s' % shortName,
                                          timeout=settings.timeOutInstall,
                                          haltOnFailure=False))
    if extraBinaries:
        extraBinaries = [extraBinaries] if isinstance(extraBinaries, str) else extraBinaries
        for binary in extraBinaries:
            factorySteps.addStep(ShellCommand(command=['./scipion', 'installb', binary, '-j', '8'],
                                              name='Install extra package %s' % binary,
                                              description='Install extra package  %s' % binary,
                                              descriptionDone='Installed extra package  %s' % binary,
                                              timeout=settings.timeOutInstall,
                                              haltOnFailure=True))
    if doTest:
        factorySteps.addStep(
            GenerateStagesCommand(command=["./scipion", "test", "--show", "--grep", shortName, '--mode', 'onlyclasses'],
                                  name="Generate Scipion test stages for %s" % shortName,
                                  description="Generating Scipion test stages for %s" % shortName,
                                  descriptionDone="Generate Scipion test stages for %s" % shortName,
                                  stagePrefix=["./scipion", "test"],
                                  haltOnFailure=False,
                                  targetTestSet=shortName))

    return factorySteps


# *****************************************************************************
#                         CLEAN-UP FACTORY
# *****************************************************************************
def cleanUpFactory(rmXmipp=False):
    cleanUpSteps = util.BuildFactory()


    cleanUpSteps.workdir = util.Property('BUILD_GROUP_HOME')
    cleanUpSteps.addStep(ShellCommand(command=['rm', '-rf', 'scipion'],
                                      name='Removing Scipion',
                                      description='Removing Scipion',
                                      descriptionDone='Scipion removed',
                                      timeout=settings.timeOutInstall))

    if rmXmipp:
        cleanUpSteps.addStep(ShellCommand(command=['rm', '-rf', 'xmipp'],
                                          name='Removing Xmipp',
                                          description='Removing Xmipp',
                                          descriptionDone='Xmipp removed',
                                          timeout=settings.timeOutInstall))



    return cleanUpSteps


# *****************************************************************************
#                         DOCS FACTORY
# *****************************************************************************
def doCommit(step):
    if step.getProperty("DOCS_REPO_STATUS") == 'clean':
        return False
    else:
        return True


def docsFactory(groupId):
    factorySteps = util.BuildFactory()
    factorySteps.workdir = settings.DOCS_BUILD_ID
    docsBranch = settings.branchsDict[groupId].get(settings.DOCS_BUILD_ID, None)
    factorySteps.addStep(Git(repourl=settings.DOCS_REPO,
                             branch=docsBranch,
                             mode='incremental',
                             name='Scipion docs repository pull',
                             haltOnFailure=True))

    factorySteps.addStep(
        ShellCommand(command=['sphinx-apidoc', '-f', '-e', '-o', 'api/',
                              util.Interpolate("%(prop:SCIPION_HOME)s/pyworkflow"),
                              util.Interpolate("%(prop:SCIPION_HOME)s/pyworkflow/tests/*")],
                     name='Generate API docs',
                     description='Generate API docs',
                     descriptionDone='Generated API docs',
                     timeout=settings.timeOutInstall))
    factorySteps.addStep(
        SetPropertyFromCommand(command='which sphinx-versioning',
                               property='sphinx-versioning',
                               name='Set property sphinx-versioning'))

    factorySteps.addStep(
        SetPropertyFromCommand(command='echo $PWD', property='DOCS_HOME',
                               name='Set property DOCS_HOME'))

    factorySteps.addStep(ShellCommand(command=["git", "add", "-A"],
                                      name='Git add docs',
                                      description='Git add docs',
                                      descriptionDone='Git added docs',
                                      timeout=settings.timeOutInstall))

    factorySteps.addStep(
        SetPropertyFromCommand(command="[[ -n $(git status -s) ]] || echo 'clean'",
                               property='DOCS_REPO_STATUS',
                               name='Set property DOCS_REPO_STATUS',
                               description='Check repo status'))

    factorySteps.addStep(ShellCommand(command=["git", "commit", "-m", "buildbot automated-update"],
                                      name='Git commit docs',
                                      description='Git commit docs',
                                      descriptionDone='Git commit docs',
                                      doStepIf=doCommit,
                                      timeout=settings.timeOutInstall))

    factorySteps.addStep(ShellCommand(command=["git", "push"],
                                      name='Git push docs to repo',
                                      description='Git push docs to repo',
                                      descriptionDone='Git push docs to repo',
                                      timeout=settings.timeOutInstall))

    factorySteps.addStep(ShellCommand(command=[util.Interpolate("%(prop:SCIPION_HOME)s/scipion"),
                                               "run", util.Property('sphinx-versioning'), 'push', '-r', docsBranch,
                                               util.Property('DOCS_HOME'), settings.DOCS_HTML_BRANCH, "."],
                                      name='Push built docs',
                                      description='Pushing built docs',
                                      descriptionDone='Pushed built docs',
                                      timeout=settings.timeOutInstall))

    return factorySteps


# #############################################################################
# ############################## BUILDERS #####################################
# #############################################################################
def getLocscaleBuilder(groupId, env):
    builderFactory = util.BuildFactory()

    locscaleEnv = {}

    if groupId == settings.PROD_GROUP_ID:
        builderFactory.addStep(installEman212)
        locscaleEnv.update(settings.EMAN212)
    else:
        locscaleEnv.update(settings.EMAN23)

    locscaleEnv.update(env)

    name = str(locscalePluginData['name'])
    return BuilderConfig(name="%s_%s" % (name, groupId),
                         tags=[groupId, name],
                         workernames=[settings.WORKER],
                         factory=pluginFactory('scipion-em-locscale', factorySteps=builderFactory),
                         workerbuilddir=groupId,
                         properties={'slackChannel': locscalePluginData.get('slackChannel', "")},
                         env=locscaleEnv)


def getScipionBuilders(groupId):
    scipionBuilders = []
    env = {"SCIPION_IGNORE_PYTHONPATH": "True",
           "SCIPION_LOCAL_CONFIG": util.Property('SCIPION_LOCAL_CONFIG')}

    if groupId != settings.SDEVEL_GROUP_ID:

        scipionBuilders.append(
            BuilderConfig(name=settings.SCIPION_INSTALL_PREFIX + groupId,
                          tags=[groupId],
                          workernames=['einstein'],
                          factory=installScipionFactory(groupId),
                          workerbuilddir=groupId,
                          properties={"slackChannel": settings.SCIPION_SLACK_CHANNEL},
                          env=env)
        )
        scipionBuilders.append(
            BuilderConfig(name=settings.SCIPION_TESTS_PREFIX + groupId,
                          tags=[groupId],
                          workernames=['einstein'],
                          factory=scipionTestFactory(groupId),
                          workerbuilddir=groupId,
                          properties={'slackChannel': settings.SCIPION_SLACK_CHANNEL},
                          env=env)
        )

        if groupId == settings.DEVEL_GROUP_ID:
            env['SCIPION_PLUGIN_JSON'] = 'plugins.json'
            scipionBuilders.append(
                BuilderConfig(name=settings.CLEANUP_PREFIX + groupId,
                              tags=[groupId],
                              workernames=['einstein'],
                              factory=cleanUpFactory(rmXmipp=True),
                              workerbuilddir=groupId,
                              properties={'slackChannel': settings.SCIPION_SLACK_CHANNEL},
                              env=env)
            )

        else:
            scipionBuilders.append(
                BuilderConfig(name=settings.CLEANUP_PREFIX + groupId,
                              tags=[groupId],
                              workernames=['einstein'],
                              factory=cleanUpFactory(),
                              workerbuilddir=groupId,
                              properties={'slackChannel': settings.SCIPION_SLACK_CHANNEL},
                              env=env)
            )

        # special locscale case, we need to install eman212

        for plugin, pluginDict in scipionPlugins.iteritems():
            moduleName = str(pluginDict.get("name", plugin.rsplit('-', 1)[-1]))
            tags = [groupId, moduleName]
            hastests = not pluginDict.get("NO_TESTS", False)
            scipionBuilders.append(
                BuilderConfig(name="%s_%s" % (moduleName, groupId),
                              tags=tags,
                              workernames=[settings.WORKER],
                              factory=pluginFactory(plugin, shortname=moduleName, doTest=hastests),
                              workerbuilddir=groupId,
                              properties={'slackChannel': scipionPlugins[plugin].get('slackChannel', "")},
                              env=env)
            )

        scipionBuilders.append(getLocscaleBuilder(groupId, env))

        if settings.branchsDict[groupId].get(settings.DOCS_BUILD_ID, None) is not None:
            scipionBuilders.append(BuilderConfig(name="%s%s" % (settings.DOCS_PREFIX, groupId),
                                                 tags=["docs", groupId],
                                                 workernames=[settings.WORKER],
                                                 factory=docsFactory(groupId),
                                                 workerbuilddir=groupId,
                                                 properties={
                                                     'slackChannel': "buildbot"},
                                                 env=env))
    else:
        scipionBuilders.append(
            BuilderConfig(name=settings.SCIPION_INSTALL_PREFIX + groupId,
                          tags=[groupId],
                          workernames=['einstein'],
                          factory=installSDevelScipionFactory(groupId),
                          workerbuilddir=groupId,
                          properties={
                              "slackChannel": settings.SCIPION_SLACK_CHANNEL},
                          env=env))
        env['SCIPION_PLUGIN_JSON'] = 'plugins.json'
        scipionBuilders.append(
            BuilderConfig(name=settings.CLEANUP_PREFIX + groupId,
                          tags=[groupId],
                          workernames=['einstein'],
                          factory=cleanUpFactory(),
                          workerbuilddir=groupId,
                          properties={
                              'slackChannel': settings.SCIPION_SLACK_CHANNEL},
                          env=env)
        )


    return scipionBuilders


# #############################################################################
# ############################## SCHEDULERS ###################################
# #############################################################################
def getScipionSchedulers(groupId):
    if groupId == settings.SDEVEL_GROUP_ID:
        scipionSchedulerNames = [settings.SCIPION_INSTALL_PREFIX + groupId,
                                 settings.CLEANUP_PREFIX + groupId]
        schedulers = []
        for name in scipionSchedulerNames:
            schedulers.append(triggerable.Triggerable(name=name,
                                                      builderNames=[name]))
            schedulers.append(
                ForceScheduler(name='%s%s' % (settings.FORCE_BUILDER_PREFIX, name),
                               builderNames=[name]))

    else:
        scipionSchedulerNames = [settings.SCIPION_INSTALL_PREFIX + groupId,
                                 settings.SCIPION_TESTS_PREFIX + groupId,
                                 settings.CLEANUP_PREFIX + groupId]

        if settings.branchsDict[groupId].get(settings.DOCS_BUILD_ID, None) is not None:
            scipionSchedulerNames.append("%s%s" % (settings.DOCS_PREFIX, groupId))
        schedulers = []
        for name in scipionSchedulerNames:
            schedulers.append(triggerable.Triggerable(name=name,
                                                      builderNames=[name]))
            schedulers.append(ForceScheduler(name='%s%s' % (settings.FORCE_BUILDER_PREFIX, name),
                                             builderNames=[name]))

        plugins = {}
        plugins.update(scipionPlugins)
        plugins.update({"scipion-em-locscale": locscalePluginData})
        for plugin, pluginDict in plugins.iteritems():
            moduleName = str(pluginDict.get("name", plugin.rsplit('-', 1)[-1]))
            schedulers.append(triggerable.Triggerable(name="%s_%s" % (moduleName, groupId),
                                                      builderNames=["%s_%s" % (moduleName, groupId)]))

            forceSchedulerName = '%s%s_%s' % (settings.FORCE_BUILDER_PREFIX, moduleName, groupId)
            schedulers.append(
                ForceScheduler(name=forceSchedulerName,
                               builderNames=["%s_%s" % (moduleName, groupId)]))

    return schedulers
