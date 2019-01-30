import json
from collections import OrderedDict

from buildbot.steps.shell import ShellCommand
from buildbot.plugins import util, steps
from buildbot.steps.source.git import Git
from buildbot.config import BuilderConfig
from buildbot.schedulers import triggerable
from buildbot.schedulers.forcesched import ForceScheduler

from settings import (MPI_BINDIR, MPI_INCLUDE, MPI_LIBDIR, CUDA_LIB, CCP4_HOME,
                      SCIPION_BUILD_ID, SCIPION_INSTALL_PREFIX, SCIPION_TESTS_PREFIX,
                      PLUGINS_JSON_FILE, CLEANUP_PREFIX, SCIPION_SLACK_CHANNEL,
                      FORCE_BUILDER_PREFIX, DEVEL_GROUP_ID, PHENIX_HOME, EMAN212,
                      gitRepoURL, timeOutInstall, branchsDict, WORKER, PROD_GROUP_ID)
from common_utils import changeConfVar, GenerateStagesCommand

# #############################################################################
# ########################## COMMANDS & UTILS #################################
# #############################################################################

with open(PLUGINS_JSON_FILE) as f:
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
def removeHomeConfig(configPath=""):
    if configPath == "":
        configPath = "$HOME/.config/scipion/scipion.conf"
    return ShellCommand(command=['bash', '-c', 'rm %s' % configPath],
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
def setNotifyAtFalse(configPath='$HOME/.config/scipion/scipion.conf'):
    return ShellCommand(
        command=['bash', '-c', 'sed -i -e '
                               '"s/MPI_LIBDIR = True/'
                               'SCIPION_NOTIFY = False/g" %s' % configPath],
        name='Cancel notifications',
        description='Do not notify usage. Server will be out of '
                    'the blacklist in order for the notify test to work',
        descriptionDone='Disable notification',
        haltOnFailure=True)

setMpiLibPath = ShellCommand(
    # command=changeConfVar.withArgs('MPI_LIBDIR', mpilibdir),
    command=changeConfVar("MPI_LIBDIR", MPI_LIBDIR, escapeSlash=True),
    name='Change MPI_LIBDIR',
    description='Add the right MPI_LIBDIR path',
    descriptionDone='Added MPI_LIBDIR',
    haltOnFailure=True)

setMpiIncludePath = ShellCommand(
    command=changeConfVar('MPI_INCLUDE', MPI_INCLUDE, escapeSlash=True),
    name='Change MPI_INCLUDE',
    description='Add the right MPI_INCLUDE path',
    descriptionDone='Added MPI_INCLUDE',
    haltOnFailure=True)

setMpiBinPath = ShellCommand(
    command=changeConfVar('MPI_BINDIR', MPI_BINDIR, escapeSlash=True),
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
    if userDataHome:
        command.append('sed -i -e '
                       '"s/SCIPION_USER_DATA = ~\/ScipionUserData/'
                       'SCIPION_USER_DATA = %s\/ScipionUserData/g" '
                       '$HOME/.config/scipion/scipion.conf' % userDataHome.replace('/', '\/'))

    return command


setScipionUserData = ShellCommand(
    command=renderScipionUserDataCmd,
    name='Set ScipionUserData dir',
    description='Using an independent ScipionUserData dir.',
    descriptionDone='Change ScipionUserData dir',
    haltOnFailure=True)

def setMotioncorrCuda(configPath='$HOME/.config/scipion/scipion.conf'):
    return ShellCommand(
    command='sed -ie "\$aMOTIONCORR_CUDA_LIB = %s" %s' % (CUDA_LIB, configPath),
    name='Set MOTIONCORR_CUDA_LIB in scipion conf',
    description='Set MOTIONCORR_CUDA_LIB in scipion conf',
    descriptionDone='Set MOTIONCORR_CUDA_LIB in scipion conf',
    haltOnFailure=True)

def setCcp4Home(configPath='$HOME/.config/scipion/scipion.conf'):
    return ShellCommand(
    command='sed -ie "\$aCCP4_HOME = %s" %s' % (CCP4_HOME, configPath),
    name='Set CCP4_HOME in scipion conf',
    description='Set CCP4_HOME in scipion conf',
    descriptionDone='Set CCP4_HOME in scipion conf',
    haltOnFailure=True)

def setPhenixHome(configPath='$HOME/.config/scipion/scipion.conf'):
    return ShellCommand(
    command='sed -ie "\$aPHENIX_HOME = %s" %s' % (PHENIX_HOME, configPath),
    name='Set PHENIX_HOME in scipion conf',
    description='Set PHENIX_HOME in scipion conf',
    descriptionDone='Set PHENIX_HOME in scipion conf',
    haltOnFailure=True)

installEman212 = ShellCommand(command=['./scipion', 'installb', 'eman-2.12'],
                              name='Install eman-2.12',
                              description='Install eman-2.12',
                              descriptionDone='Installed eman-2.12',
                              timeout=timeOutInstall,
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


def addScipionGitAndConfigSteps(factorySteps, groupId):
    """ The initial steps are common in all builders.
         1. git pull in a certain branch.
         2. remove scipion.config files.
         3. regenerate scipion.config files
         4. set notify at False
         5. set dataTests folder to a common dir (to save space)
         6. set ScipionUserData to an internal folder (to allow branch-dependent project inspection)
    """
    factorySteps.addStep(Git(repourl=gitRepoURL,
                             branch=branchsDict[groupId].get(SCIPION_BUILD_ID, None),
                             mode='incremental',
                             name='Scipion Git Repository Pull',
                             haltOnFailure=True))

    factorySteps.addStep(removeScipionConf)

    factorySteps.addStep(removeHomeConfig(configPath=util.Property('SCIPION_LOCAL_CONFIG')))
    factorySteps.addStep(configScipion)
    factorySteps.addStep(setNotifyAtFalse(configPath=util.Property('SCIPION_LOCAL_CONFIG')))
    factorySteps.addStep(setMpiLibPath)
    factorySteps.addStep(setMpiBinPath)
    factorySteps.addStep(setMpiIncludePath)
    factorySteps.addStep(setDataTestsDir)
    # factorySteps.addStep(removeScipionUserData)  # to avoid old tests when are renamed
    factorySteps.addStep(setScipionUserData)

    return factorySteps


# Command to install Scipion and/or recompile Xmipp
installScipion = ShellCommand(command=['./scipion', 'install', '-j', '8'],
                              name='Scipion Install',
                              description='Compiling everything that needs re-compiling',
                              descriptionDone='Install Scipion',
                              timeout=timeOutInstall,
                              haltOnFailure=True)


# #############################################################################
# ############################## FACTORIES ####################################
# #############################################################################

# *****************************************************************************
#                         INSTALL SCIPION FACTORY
# *****************************************************************************
def installScipionFactory(groupId):
    installScipionFactorySteps = util.BuildFactory()
    installScipionFactorySteps.workdir = SCIPION_BUILD_ID
    installScipionFactorySteps = addScipionGitAndConfigSteps(installScipionFactorySteps,
                                                             groupId)
    installScipionFactorySteps.addStep(ShellCommand(command=['echo', 'SCIPION_LOCAL_CONFIG',
                                               util.Property('SCIPION_LOCAL_CONFIG')],
                                      name='Echo SCIPION_LOCAL_CONFIG',
                                      description='Echo SCIPION_LOCAL_CONFIG',
                                      descriptionDone='Echo SCIPION_LOCAL_CONFIG',
                                      timeout=300
                                      ))
    installScipionFactorySteps.addStep(installScipion)
    installScipionFactorySteps.addStep(
        ShellCommand(command=['ls', '-1', 'software/lib'],
                     name='Test software/lib',
                     description='Test if software/lib created after installing scipion',
                     descriptionDone='Test scipion installation',
                     haltOnFailure=True))
    installScipionFactorySteps.addStep(
        steps.JSONStringDownload(scipionPlugins, workerdest="plugins.json"))
    installScipionFactorySteps.addStep(setMotioncorrCuda(configPath=util.Property('SCIPION_LOCAL_CONFIG')))
    installScipionFactorySteps.addStep(setPhenixHome(configPath=util.Property('SCIPION_LOCAL_CONFIG')))
    installScipionFactorySteps.addStep(setCcp4Home(configPath=util.Property('SCIPION_LOCAL_CONFIG')))
    return installScipionFactorySteps

# *****************************************************************************
#                         SCIPION TEST FACTORY
# *****************************************************************************
def scipionTestFactory():
    scipionTestSteps = util.BuildFactory()
    scipionTestSteps.workdir = util.Property('SCIPION_HOME')

    # add TestRelionExtractStreaming manually because it needs eman 2.12
    wfRelionExtractStreaming = 'pyworkflow.tests.em.workflows.test_workflow_streaming.TestRelionExtractStreaming'

    # blacklist all queue tests and TestRelionExtractStreaming because we add it manually
    blacklist = ["pyworkflow.tests.em.workflows.test_parallel_gpu_queue.Test_noQueue_Small",
                 "pyworkflow.tests.em.workflows.test_parallel_gpu_queue.Test_noQueue_ALL",
                 "pyworkflow.tests.em.workflows.test_parallel_gpu_queue.Test_Queue_Small",
                 "pyworkflow.tests.em.workflows.test_parallel_gpu_queue.Test_Queue_ALL",
                 "pyworkflow.tests.em.workflows.test_workflow_existing.TestXmippWorkflow"]
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
                              blacklist=blacklist,
                              stageEnvs={wfRelionExtractStreaming: EMAN212}))

    return scipionTestSteps


# *****************************************************************************
#                         PLUGIN FACTORY
# *****************************************************************************
def pluginFactory(pluginName, factorySteps=None, shortname=None):
    factorySteps = factorySteps or util.BuildFactory()
    factorySteps.workdir = util.Property('SCIPION_HOME')
    shortName = shortname or str(pluginName.rsplit('-', 1)[-1])  # todo: get module names more properly?
    factorySteps.addStep(ShellCommand(command=['./scipion', 'installp', '-p', pluginName],
                                      name='Install plugin %s' % shortName,
                                      description='Install plugin %s' % shortName,
                                      descriptionDone='Installed plugin %s' % shortName,
                                      timeout=timeOutInstall,
                                      haltOnFailure=True))
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
def cleanUpFactory():
    cleanUpSteps = util.BuildFactory()
    cleanUpSteps.workdir = util.Property('BUILD_GROUP_HOME')

    cleanUpSteps.addStep(ShellCommand(command=['rm', '-rf', 'scipion'],
                                      name='Removing Scipion',
                                      description='Removing Scipion',
                                      descriptionDone='Scipion removed',
                                      timeout=timeOutInstall))

    cleanUpSteps.addStep(ShellCommand(command=['rm', '-rf', 'xmipp'],
                                      name='Removing Xmipp',
                                      description='Removing Xmipp',
                                      descriptionDone='Xmipp removed',
                                      timeout=timeOutInstall))

    return cleanUpSteps


# #############################################################################
# ############################## BUILDERS #####################################
# #############################################################################
def getLocscaleBuilder(groupId, env):
    builderFactory = util.BuildFactory()
    builderFactory.addStep(installEman212)
    locscaleEnv = {}
    locscaleEnv.update(env)
    locscaleEnv.update(EMAN212)
    name = str(locscalePluginData['name'])
    return BuilderConfig(name="%s_%s" % (name, groupId),
                      tags=[groupId, name],
                      workernames=[WORKER],
                      factory=pluginFactory('scipion-em-locscale', factorySteps=builderFactory),
                      workerbuilddir=groupId,
                      properties={'slackChannel': locscalePluginData.get('slackChannel', "")},
                      env=locscaleEnv)

def getScipionBuilders(groupId):
    scipionBuilders = []
    env = {"SCIPION_IGNORE_PYTHONPATH": "True",
           "SCIPION_LOCAL_CONFIG": util.Property('SCIPION_LOCAL_CONFIG')}
    scipionBuilders.append(
        BuilderConfig(name=SCIPION_INSTALL_PREFIX + groupId,
                      tags=[groupId],
                      workernames=['einstein'],
                      factory=installScipionFactory(groupId),
                      workerbuilddir=groupId,
                      properties={"slackChannel": SCIPION_SLACK_CHANNEL},
                      env=env)
    )
    scipionBuilders.append(
        BuilderConfig(name=SCIPION_TESTS_PREFIX + groupId,
                      tags=[groupId],
                      workernames=['einstein'],
                      factory=scipionTestFactory(),
                      workerbuilddir=groupId,
                      properties={'slackChannel': SCIPION_SLACK_CHANNEL},
                      env=env)
    )

    scipionBuilders.append(
        BuilderConfig(name=CLEANUP_PREFIX + groupId,
                      tags=[groupId],
                      workernames=['einstein'],
                      factory=cleanUpFactory(),
                      workerbuilddir=groupId,
                      properties={'slackChannel': SCIPION_SLACK_CHANNEL},
                      env=env)
    )
    if groupId == DEVEL_GROUP_ID:
        env['SCIPION_PLUGIN_JSON'] = 'plugins.json'

    # special locscale case, we need to install eman212

    for plugin in scipionPlugins:
        moduleName = str(plugin.rsplit('-', 1)[-1])
        tags = [groupId, moduleName]
        scipionBuilders.append(
            BuilderConfig(name="%s_%s" % (moduleName, groupId),
                          tags=tags,
                          workernames=['einstein'],
                          factory=pluginFactory(plugin),
                          workerbuilddir=groupId,
                          properties={'slackChannel': scipionPlugins[plugin].get('slackChannel', "")},
                          env=env)
        )

    scipionBuilders.append(getLocscaleBuilder(groupId, env))

    return scipionBuilders


# #############################################################################
# ############################## SCHEDULERS ###################################
# #############################################################################
def getScipionSchedulers(groupId):
    scipionSchedulerNames = [SCIPION_INSTALL_PREFIX + groupId,
                             SCIPION_TESTS_PREFIX + groupId,
                             CLEANUP_PREFIX + groupId]
    schedulers = []
    for name in scipionSchedulerNames:
        schedulers.append(triggerable.Triggerable(name=name,
                                                  builderNames=[name]))
        schedulers.append(ForceScheduler(name='%s%s' % (FORCE_BUILDER_PREFIX, name),
                                         builderNames=[name]))

    plugins = {}
    plugins.update(scipionPlugins)
    plugins.update({"scipion-em-locscale": locscalePluginData})
    for plugin in plugins:
        moduleName = str(plugin.rsplit('-', 1)[-1])
        schedulers.append(triggerable.Triggerable(name="%s_%s" % (moduleName, groupId),
                                                  builderNames=["%s_%s" % (moduleName, groupId)]))

        forceSchedulerName = '%s%s_%s' % (FORCE_BUILDER_PREFIX, moduleName, groupId)
        schedulers.append(
            ForceScheduler(name=forceSchedulerName,
                           builderNames=["%s_%s" % (moduleName, groupId)]))

    return schedulers