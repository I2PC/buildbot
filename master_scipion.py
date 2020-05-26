import json
import os
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


with open(settings.SDEVELPLUGINS_JSON_FILE) as f:
    # read in order, since we have taken into account dependencies in
    # between plugins when completing the json file
    scipionSdevelPlugins = json.load(f, object_pairs_hook=OrderedDict)
    xmippSdevelPluginData = scipionSdevelPlugins.pop('scipion-em-xmipp')
    locscaleSdevelPluginData = scipionSdevelPlugins.pop("scipion-em-locscale")
    pyworkflowPlugin = scipionSdevelPlugins.pop("scipion-pyworkflow")
    pwemPlugin = scipionSdevelPlugins.pop("scipion-em")

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
        'sed -ie "\$aMOTIONCORR_CUDA_LIB = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.MOTIONCOR2_CUDA_LIB)),
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


setEM_ROOTSdevel = ShellCommand(
    command=changeConfVar('EM_ROOT', settings.EM_ROOT,
                          file=settings.SDEVEL_SCIPION_CONFIG_PATH,
                          escapeSlash=True),
    name='Change EM_ROOT',
    description='Add the right EM_ROOT path',
    descriptionDone='Added EM_ROOT',
    haltOnFailure=True)

setCcp4HomeSdevel = ShellCommand(
    command=changeConfVar('CCP4_HOME', settings.CCP4_HOME,
                          file=settings.SDEVEL_SCIPION_CONFIG_PATH,
                          escapeSlash=True),
    name='Change CCP4_HOME',
    description='Add the right CCP4_HOME path',
    descriptionDone='Added CCP4_HOME',
    haltOnFailure=True)

setCcp4HomeSProd = ShellCommand(
    command=util.Interpolate('sed -ie "\$aCCP4_HOME = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.CCP4_HOME)),
    name='Add the right CCP4_HOME path',
    description='Add the CCP4_HOME path',
    descriptionDone='Add the CCP4_HOME path',
    haltOnFailure=True)

setNYSBC_3DFSC_HOME = ShellCommand(
    command=util.Interpolate('sed -ie "\$aNYSBC_3DFSC_HOME = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.NYSBC_3DFSC_HOME)),
    name='Set NYSBC_3DFSC_HOME in scipion conf',
    description='Set NYSBC_3DFSC_HOME in scipion conf',
    descriptionDone='Set NYSBC_3DFSC_HOME in scipion conf',
    haltOnFailure=True)

setNYSBC_3DFSC_HOMESdevel = ShellCommand(
    command=changeConfVar('FSC3D_HOME', settings.NYSBC_3DFSC_HOME,
                          file=settings.SDEVEL_SCIPION_CONFIG_PATH,
                          escapeSlash=True),
    name='Change NYSBC_3DFSC_HOME',
    description='Add the right NYSBC_3DFSC_HOME path',
    descriptionDone='Added NYSBC_3DFSC_HOME',
    haltOnFailure=True)

setCryoloModel = ShellCommand(
    command=util.Interpolate('sed -ie "\$aCRYOLO_NS_GENERIC_MODEL = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.CRYOLO_NS_GENERIC_MODEL)),
    name='Set CRYOLO_GENERIC_MODEL in scipion conf',
    description='Set CRYOLO_GENERIC_MODEL in scipion conf',
    descriptionDone='Set CRYOLO_GENERIC_MODEL in scipion conf',
    haltOnFailure=True)

setCryoloModelSdevel = ShellCommand(
    command=changeConfVar('CRYOLO_NS_GENERIC_MODEL', settings.CRYOLO_NS_GENERIC_MODEL,
                          file=settings.SDEVEL_SCIPION_CONFIG_PATH,
                          escapeSlash=True),
    name='Change CRYOLO_NS_GENERIC_MODEL',
    description='Add the right CRYOLO_NS_GENERIC_MODEL path',
    descriptionDone='Added CRYOLO_NS_GENERIC_MODEL',
    haltOnFailure=True)


setCryoloProdModelSdevel = ShellCommand(
    command=util.Interpolate('sed -ie "\$aCRYOLO_NS_GENERIC_MODEL = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.CRYOLO_NS_GENERIC_MODEL)),
    name='Set CRYOLO_NS_GENERIC_MODEL in scipion conf',
    description='Set CRYOLO_NS_GENERIC_MODEL in scipion conf',
    descriptionDone='Set CRYOLO_NS_GENERIC_MODEL in scipion conf',
    haltOnFailure=True)

setCryoloEnvActivation = ShellCommand(
    command=util.Interpolate('sed -ie "\$aCRYOLO_ENV_ACTIVATION = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.CRYOLO_ENV_ACTIVATION)),
    name='Set CRYOLO_ENV_ACTIVATION in scipion conf',
    description='Set CRYOLO_ENV_ACTIVATION in scipion conf',
    descriptionDone='Set CRYOLO_ENV_ACTIVATION in scipion conf',
    haltOnFailure=True)

setCryoloEnvActivationSdevel = ShellCommand(
    command=changeConfVar('CRYOLO_ENV_ACTIVATION', settings.CRYOLO_ENV_ACTIVATION,
                          file=settings.SDEVEL_SCIPION_CONFIG_PATH,
                          escapeSlash=True),
    name='Change CRYOLO_ENV_ACTIVATION',
    description='Add the right CRYOLO_ENV_ACTIVATION path',
    descriptionDone='Added CRYOLO_ENV_ACTIVATION',
    haltOnFailure=True)

setCryoloCuda = ShellCommand(
    command=util.Interpolate(
        'sed -ie "\$aCRYOLO_CUDA_LIB = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.CRYOLO_CUDA_LIB)),
    name='Add CRYOLO_CUDA_LIB in scipion conf',
    description='Add CRYOLO_CUDA_LIB in scipion conf',
    descriptionDone='Add CRYOLO_CUDA_LIB in scipion conf',
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

setPhenixHomeSdevel = ShellCommand(
    command=changeConfVar('PHENIX_HOME', settings.PHENIX_HOME,
                          file=settings.SDEVEL_SCIPION_CONFIG_PATH,
                          escapeSlash=True),
    name='Change PHENIX_HOME',
    description='Add the right PHENIX_HOME path',
    descriptionDone='Added PHENIX_HOME',
    haltOnFailure=True)

setPhenixHomeSProd = ShellCommand(
    command=util.Interpolate(
        'sed -ie "\$aPHENIX_HOME = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.PHENIX_HOME)),
    name='Add PHENIX_HOME in scipion conf',
    description='Add PHENIX_HOME in scipion conf',
    descriptionDone='Add PHENIX_HOME in scipion conf',
    haltOnFailure=True)


setCryosparcDir = ShellCommand(
    command=util.Interpolate(
        'sed -ie "\$aCRYOSPARC_DIR = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.CRYOSPARC_DIR)),
    name='Set CRYOSPARC_DIR in scipion conf',
    description='Set CRYOSPARC_DIR in scipion conf',
    descriptionDone='Set CRYOSPARC_DIR in scipion conf',
    haltOnFailure=True)

setCryosparcHomeSdevel = ShellCommand(
    command=changeConfVar('CRYOSPARC_HOME', settings.CRYOSPARC_DIR,
                          file=settings.SDEVEL_SCIPION_CONFIG_PATH,
                          escapeSlash=True),
    name='Change CRYOSPARC_HOME',
    description='Add the right CRYOSPARC_HOME path',
    descriptionDone='Added CRYOSPARC_HOME',
    haltOnFailure=True)

setCryosparcHomeSProd = ShellCommand(
    command=changeConfVar('CRYOSPARC_HOME', settings.CRYOSPARC_DIR,
                          file=settings.SPROD_SCIPION_CONFIG_PATH,
                          escapeSlash=True),
    name='Change CRYOSPARC_HOME',
    description='Add the right CRYOSPARC_HOME path',
    descriptionDone='Added CRYOSPARC_HOME',
    haltOnFailure=True)

setCryosparcProjectDir = ShellCommand(
    command=changeConfVar('CRYO_PROJECTS_DIR', settings.CRYOSPARC_DIR +
                          'scipion_projects',
                          file=settings.SDEVEL_SCIPION_CONFIG_PATH,
                          escapeSlash=True),
    name='Change CRYO_PROJECTS_DIR',
    description='Add the right CRYO_PROJECTS_DIR path',
    descriptionDone='Added CRYO_PROJECTS_DIR',
    haltOnFailure=True)

setProdCryosparcProjectDir = ShellCommand(
    command=changeConfVar('CRYO_PROJECTS_DIR', settings.CRYOSPARC_DIR +
                          'scipion_projects',
                          file=settings.SPROD_SCIPION_CONFIG_PATH,
                          escapeSlash=True),
    name='Change CRYO_PROJECTS_DIR',
    description='Add the right CRYO_PROJECTS_DIR path',
    descriptionDone='Added CRYO_PROJECTS_DIR',
    haltOnFailure=True)

setCryosparcUser = ShellCommand(
    command=util.Interpolate(
        'sed -ie "\$aCRYOSPARC_USER = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.CRYOSPARC_USER)),
    name='Set CRYOSPARC_USER in scipion conf',
    description='Set CRYOSPARC_USER in scipion conf',
    descriptionDone='Set CRYOSPARC_USER in scipion conf',
    haltOnFailure=True)


setMotincor2Bin = ShellCommand(
    command=changeConfVar('MOTIONCOR2_BIN', settings.MOTIONCOR2_BIN,
                          file=settings.SDEVEL_SCIPION_CONFIG_PATH,
                          escapeSlash=True),
    name='Change MOTIONCOR2_BIN',
    description='Add the right MOTIONCOR2_BIN file',
    descriptionDone='Added MOTIONCOR2_BIN',
    haltOnFailure=True)

setGctfBin = ShellCommand(
    command=changeConfVar('GCTF', settings.GCTF,
                          file=settings.SDEVEL_SCIPION_CONFIG_PATH,
                          escapeSlash=True),
    name='Change GCTF binary',
    description='Add the right GCTF binary',
    descriptionDone='Added GCTF binary',
    haltOnFailure=True)

setMotincor2BinProd = ShellCommand(
    command=util.Interpolate(
        'sed -ie "\$aMOTIONCOR2_BIN = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.MOTIONCOR2_BIN)),
    name='Add the right MOTIONCOR2_BIN file',
    description='Add the right MOTIONCOR2_BIN file',
    descriptionDone='Add the right MOTIONCOR2_BIN file',
    haltOnFailure=True)

setGCTFBinProd = ShellCommand(
    command=util.Interpolate(
        'sed -ie "\$aGCTF = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.GCTF)),
    name='Add the right GCTF Bin file',
    description='Add the right GCTF bin file',
    descriptionDone='Add the right GCTF bin file',
    haltOnFailure=True)

setGCTFCuda = ShellCommand(
    command=util.Interpolate(
        'sed -ie "\$aGCTF_CUDA_LIB = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.GCTF_CUDA_LIB)),
    name='Add the GCTF_CUDA_LIB',
    description='Add the GCTF_CUDA_LIB',
    descriptionDone='Add the GCTF_CUDA_LIB',
    haltOnFailure=True)

setGautomatchBinProd = ShellCommand(
    command=util.Interpolate(
        'sed -ie "\$aGAUTOMATCH = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.GAUTOMATCH)),
    name='Add the right GAUTOMATCH Bin file',
    description='Add the right GAUTOMATCH bin file',
    descriptionDone='Add the right GAUTOMATCH bin file',
    haltOnFailure=True)

setSPIDERBinProd = ShellCommand(
    command=util.Interpolate(
        'sed -ie "\$aSPIDER = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.SPIDER)),
    name='Add the right SPIDER Bin file',
    description='Add the right SPIDER bin file',
    descriptionDone='Add the right SPIDER bin file',
    haltOnFailure=True)

setSPIDER_MPIProd = ShellCommand(
    command=util.Interpolate(
        'sed -ie "\$aSPIDER_MPI = {}" %(prop:SCIPION_LOCAL_CONFIG)s'.format(settings.SPIDER_MPI)),
    name='Add the right SPIDER_MPI file',
    description='Add the right SPIDER_MPI file',
    descriptionDone='Add the right SPIDER_MPI file',
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
removeCryosParcProjectCmd = ('rm -rf ' + settings.CRYOSPARC_DIR +
                             '/scipion_projects/* ; ')
removeCryosParcProjectTest = ShellCommand(
    command=['bash', '-c', removeCryosParcProjectCmd],
    name='Clean CryosPARC projects',
    description='Delete CryosPARC projects',
    descriptionDone='Delete CryosPARC projects',
    haltOnFailure=False)

# Command to install Scipion and/or recompile Xmipp
installScipion = ShellCommand(command=['./scipion', 'install', '-j', '8'],
                              name='Scipion Install',
                              description='Compiling everything that needs re-compiling',
                              descriptionDone='Install Scipion',
                              timeout=settings.timeOutInstall,
                              haltOnFailure=True)


# Command to activate the Anaconda virtual environment
EnvActivation = ShellCommand(command=settings.CONDA_ACTIVATION_CMD.split(),
                              name='Conda activation command',
                              description='Conda activation command',
                              descriptionDone='Conda activation command',
                              timeout=settings.timeOutInstall,
                              haltOnFailure=True)

# Command to change the virtual environment to install the new version of Scipion
setScipionEnv = ShellCommand(command=settings.SCIPION_ENV_ACTIVATION.split(),
                              name='Setting Scipion Environ',
                              description='Setting Scipion Environ',
                              descriptionDone='Setting Scipion Environ',
                              timeout=settings.timeOutInstall,
                              haltOnFailure=True)

installSdevelScipionPyworkflow = 'cd scipion-pyworkflow ; python -m pip install -e .'
installSdevelScipionEM = 'cd scipion-em ; python -m pip install -e .'
installSdevelScipionApp = 'cd scipion-app ; python -m pip install -e .'
createSoftwareEM = 'mkdir -p software/em && mkdir -p software/lib && mkdir -p software/bindings'

removeScipionModules = ShellCommand(
    command=['bash', '-c',
             'rm -rf scipion-em ; '
             'rm -rf scipion-pyworkflow ; '
             'rm -rf scipion-app ; '
             'rm -rf software ; '
             ],
    name='Clean scipion modules',
    description='Delete the scipion modules to get the last versions',
    descriptionDone='Remove EM scipion modules',
    haltOnFailure=False)

sdevelScipionConfig = ('python -m scipion config --notify --overwrite && cp ' +
                      settings.SDEVEL_SCIPION_HOME +
                       '/config/scipion.conf' + ' ' +
                       settings.SDEVEL_SCIPION_CONFIG_PATH)

sdevelMoveScipionConfig = ('cp ' + settings.SDEVEL_SCIPION_CONFIG_PATH + ' ' +
                            settings.SDEVEL_SCIPION_HOME + '/config/scipion.conf')

sprodScipionConfig = ('./scipion3 config --notify --overwrite && cp ' +
                      settings.SPROD_SCIPION_HOME +
                       '/config/scipion.conf' + ' ' +
                       settings.SPROD_SCIPION_CONFIG_PATH)

sprodMoveScipionConfig = ('cp ' + settings.SPROD_SCIPION_CONFIG_PATH + ' ' +
                            settings.SPROD_SCIPION_HOME + '/config/scipion.conf')


# Update the Scipion web site
updateWebSiteCmd = 'python ' + settings.BUILDBOT_HOME + 'updateScipionSite.py'


def addScipionGitAndConfigSteps(factorySteps, groupId):
    """ The initial steps are common in all builders.
         1. git pull in a certain branch.
         2. remove scipion.config files.
         3. regenerate scipion.config files
         4. set notify at False
         5. set dataTests folder to a common dir (to save space)
         6. set ScipionUserData to an internal folder (to allow branch-dependent project inspection)
    """
    factorySteps.addStep(Git(repourl=settings.gitRepoURL,
                             branch=settings.branchsDict[groupId].get(settings.SCIPION_BUILD_ID, None),
                             mode='incremental',
                             name='Scipion Git Repository Pull',
                             haltOnFailure=True))

    factorySteps.addStep(removeScipionConf)
    factorySteps.addStep(removeHomeConfig)
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
         1. Remove scipion-em, scipion-app and scipion-pyworkflow, software-em to get the last version
         2. git pull scipion-app, scipion-pyworkflow, scipion-em.
         3. Create the software/em folder
    """
    factorySteps.addStep(removeScipionModules)
    factorySteps.addStep(removeCryosParcProjectTest)

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

    return factorySteps


class ScipionCommandStep(ShellCommand):
    def __init__(self, command='', name='', description='',
                 descriptionDone='', timeout=settings.timeOutInstall,
                 haltOnFailure=True, **kwargs):
        kwargs['command'] = [
            'bash', '-c', '%s; %s' % (settings.SCIPION_ENV_ACTIVATION, command)
        ]
        kwargs['name'] = name
        kwargs['description'] = description
        kwargs['descriptionDone'] = descriptionDone
        kwargs['timeout'] = timeout
        kwargs['haltOnFailure'] = haltOnFailure

        ShellCommand.__init__(self, **kwargs)


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
    installScipionFactorySteps.addStep(setCryoloCuda)
    installScipionFactorySteps.addStep(setPhenixHome)
    installScipionFactorySteps.addStep(setCryosparcDir)
    installScipionFactorySteps.addStep(setCryosparcUser)
    installScipionFactorySteps.addStep(setMotincor2Bin)
    installScipionFactorySteps.addStep(setCcp4Home)
    installScipionFactorySteps.addStep(setNYSBC_3DFSC_HOME)
    # installScipionFactorySteps.addStep(setCryoloModel)
    installScipionFactorySteps.addStep(setCryoloEnvActivation)
    installScipionFactorySteps.addStep(setCondaActivation)
    return installScipionFactorySteps


def installProdScipionFactory(groupId):
    installScipionFactorySteps = util.BuildFactory()
    installScipionFactorySteps.workdir = settings.SCIPION_BUILD_ID

    installScipionFactorySteps.addStep(
        ShellCommand(command=['echo', 'SCIPION_LOCAL_CONFIG',
                              util.Property('SCIPION_LOCAL_CONFIG')],
                     name='Echo SCIPION_LOCAL_CONFIG',
                     description='Echo SCIPION_LOCAL_CONFIG',
                     descriptionDone='Echo SCIPION_LOCAL_CONFIG',
                     timeout=settings.timeOutShort
                     ))

    # Install Scipion by the installer script
    # Downloading the installer from pypi and install it
    installScipionFactorySteps.addStep((ShellCommand(command=['pip', 'install', 'scipion-installer==1.0.0b0'],
                                                    name='Installing scipion-installer from pypi',
                                                    description='Installing scipion-installer from pypi',
                                                    descriptionDone='Installing scipion-installer from pypi',
                                                    timeout=settings.timeOutShort
                                                    )))

    # Install Scipion
    scipionHome = settings.SPROD_SCIPION_HOME
    installScipionFactorySteps.addStep(
        (ShellCommand(command=['installscipion', scipionHome, '-noAsk', '-n',
                               'prodEnv', '-conda'],
                      name='Install Scipion',
                      description='Install Scipion',
                      descriptionDone='Install Scipion',
                      timeout=settings.timeOutShort
                      )))

    installScipionFactorySteps.addStep(
        (ShellCommand(command=['chmod', '777', '-R', settings.SPROD_ENV_PATH],
                      name='Change the permission of environment folder',
                      description='Change the permission of environment folder',
                      descriptionDone='Change the permission of environment folder',
                      timeout=settings.timeOutShort
                      )))

    installScipionFactorySteps.addStep(
        steps.JSONStringDownload(dict(scipionSdevelPlugins, **{
            "scipion-em-locscale": locscaleSdevelPluginData}),
                                 workerdest="plugins.json"))

    # Scipion config
    installScipionFactorySteps.addStep(removeScipionConf)
    installScipionFactorySteps.addStep(removeHomeConfig)
    installScipionFactorySteps.addStep(
        ShellCommand(command=sprodScipionConfig,
                           name='Scipion Config',
                           description='Create installation configuration files',
                           descriptionDone='Scipion config',
                           haltOnFailure=True))

    installScipionFactorySteps.addStep(setScipionUserData)
    installScipionFactorySteps.addStep(setNotifyAtFalse)
    installScipionFactorySteps.addStep(setGeneralCuda)
    installScipionFactorySteps.addStep(setMpiLibPath)
    installScipionFactorySteps.addStep(setMpiBinPath)
    installScipionFactorySteps.addStep(setMpiIncludePath)
    installScipionFactorySteps.addStep(setDataTestsDir)
    # Activating the Anaconda environment
    # Set the anaconda environment
    installScipionFactorySteps.addStep(setMotioncorrCuda)
    installScipionFactorySteps.addStep(setCryoloCuda)
    installScipionFactorySteps.addStep(setCondaActivation)

    installScipionFactorySteps.addStep(setScipionEnvActivation)
    installScipionFactorySteps.addStep(setCcp4HomeSProd)
    # installScipionFactorySteps.addStep(setNYSBC_3DFSC_HOMESdevel)
    # installScipionFactorySteps.addStep(setCryoloModelSdevel)
    # installScipionFactorySteps.addStep(setCryoloEnvActivationSdevel)
    installScipionFactorySteps.addStep(setCryosparcDir)
    installScipionFactorySteps.addStep(setProdCryosparcProjectDir)
    installScipionFactorySteps.addStep(setCryosparcHomeSProd)
    installScipionFactorySteps.addStep(setCryosparcUser)
    installScipionFactorySteps.addStep(setMotincor2BinProd)
    installScipionFactorySteps.addStep(setGCTFBinProd)
    installScipionFactorySteps.addStep(setGCTFCuda)
    installScipionFactorySteps.addStep(setGautomatchBinProd)
    installScipionFactorySteps.addStep(setSPIDERBinProd)
    installScipionFactorySteps.addStep(setSPIDER_MPIProd)
    installScipionFactorySteps.addStep(setPhenixHomeSProd)
    installScipionFactorySteps.addStep(
        ScipionCommandStep(command=sprodMoveScipionConfig,
                           name='Move Scipion Config file',
                           description='Move Scipion Config file',
                           descriptionDone='Move Scipion Config file',
                           haltOnFailure=True))

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
    # Install scipion-pyworkflow
    installScipionFactorySteps.addStep(ScipionCommandStep(command=installSdevelScipionPyworkflow,
                                                          name='Installing scipion-pyworkflow...',
                                                          description='Install Scipion-pyworkflow as devel mode',
                                                          descriptionDone='Install Scipion-pyworkflow',
                                                          ))

    # # Install scipion-em
    installScipionFactorySteps.addStep(
        ScipionCommandStep(command=installSdevelScipionEM,
                           name='Installing scipion-em...',
                           description='Install Scipion-em as devel mode',
                           descriptionDone='Install Scipion-pyworkflow',
                           ))
    #Install scipion-app
    installScipionFactorySteps.addStep(
        ScipionCommandStep(command=installSdevelScipionApp,
                           name='Installing scipion-app...',
                           description='Install Scipion-pyworkflow as devel mode',
                           descriptionDone='Install Scipion-pyworkflow',
                           ))

    installScipionFactorySteps.addStep(
        ShellCommand(command=["bash", "-c", createSoftwareEM],
                           name='Creating software/em folder...',
                           description='Creating software/em folder in SCIPION_HOME',
                           descriptionDone='Creating software/em folder',
                           ))


    installScipionFactorySteps.addStep(
        steps.JSONStringDownload(dict(scipionSdevelPlugins, **{"scipion-em-locscale": locscaleSdevelPluginData}),
            workerdest="plugins.json"))

    installScipionFactorySteps.addStep(removeScipionConf)
    installScipionFactorySteps.addStep(removeHomeConfig)
    installScipionFactorySteps.addStep(ScipionCommandStep(command=sdevelScipionConfig,
                                                          name='Scipion Config',
                                                          description='Create installation configuration files',
                                                          descriptionDone='Scipion config',
                                                          haltOnFailure=True))

    installScipionFactorySteps.addStep(setEM_ROOTSdevel)
    installScipionFactorySteps.addStep(setScipionUserData)
    installScipionFactorySteps.addStep(setNotifyAtFalse)
    installScipionFactorySteps.addStep(setGeneralCuda)
    installScipionFactorySteps.addStep(setMpiLibPath)
    installScipionFactorySteps.addStep(setMpiBinPath)
    installScipionFactorySteps.addStep(setMpiIncludePath)
    installScipionFactorySteps.addStep(setDataTestsDir)
    # Activating the Anaconda environment
    # Set the anaconda environment
    installScipionFactorySteps.addStep(setMotioncorrCuda)
    installScipionFactorySteps.addStep(setCryoloCuda)
    installScipionFactorySteps.addStep(setCondaActivation)
    installScipionFactorySteps.addStep(setScipionEnvActivation)
    installScipionFactorySteps.addStep(setCcp4HomeSdevel)
    #installScipionFactorySteps.addStep(setNYSBC_3DFSC_HOMESdevel)
    #installScipionFactorySteps.addStep(setCryoloModelSdevel)
    #installScipionFactorySteps.addStep(setCryoloEnvActivationSdevel)
    installScipionFactorySteps.addStep(setCryosparcDir)
    installScipionFactorySteps.addStep(setCryosparcProjectDir)
    installScipionFactorySteps.addStep(setCryosparcHomeSdevel)
    installScipionFactorySteps.addStep(setGctfBin)
    installScipionFactorySteps.addStep(setGCTFCuda)
    installScipionFactorySteps.addStep(setCryosparcUser)
    installScipionFactorySteps.addStep(setMotincor2Bin)
    installScipionFactorySteps.addStep(setPhenixHomeSdevel)
    installScipionFactorySteps.addStep(
    ScipionCommandStep(command=sdevelMoveScipionConfig,
                       name='Move Scipion Config file',
                       description='Move Scipion Config file',
                       descriptionDone='Move Scipion Config file',
                       haltOnFailure=True))


    return installScipionFactorySteps


# *****************************************************************************
#                         SCIPION TEST FACTORY
# *****************************************************************************
def scipionTestFactory(groupId):


    scipionTestSteps = util.BuildFactory()
    scipionTestSteps.workdir = util.Property('SCIPION_HOME')

    emanVar = settings.EMAN212 if groupId == settings.PROD_GROUP_ID else settings.EMAN23

    if groupId == settings.PROD_GROUP_ID:
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
    elif groupId == settings.SDEVEL_GROUP_ID:
        scipionTestSteps.addStep(ShellCommand(
            command=['echo', 'SCIPION_HOME: ', util.Property('SCIPION_HOME')],
            name='Echo scipion home',
            description='Echo scipion home',
            descriptionDone='Echo scipion home',
            timeout=settings.timeOutExecute))

        shortNames = ["pyworkflowtests", "pwem"]

        for shortName in shortNames:

            pluginsTestShowcmd = ["bash", "-c", settings.SCIPION_ENV_ACTIVATION +
                                 " ; " + "python -m scipion test --show --grep "
                                  + shortName + " --mode onlyclasses"]

            scipionTestSteps.addStep(
                GenerateStagesCommand(command=pluginsTestShowcmd,
                                      name="Generate Scipion test stages for %s" % shortName,
                                      description="Generating Scipion test stages for %s" % shortName,
                                      descriptionDone="Generate Scipion test stages for %s" % shortName,
                                      stagePrefix=[settings.SCIPION_CMD, "test"],
                                      haltOnFailure=False,
                                      targetTestSet=shortName))

    return scipionTestSteps


# *****************************************************************************
#                         PLUGIN FACTORY
# *****************************************************************************
def pluginFactory(groupId, pluginName, factorySteps=None, shortname=None,
                  doInstall=True, extraBinaries=[], doTest=True,
                  deleteVirtualEnv='', binToRemove=[]):
    factorySteps = factorySteps or util.BuildFactory()
    factorySteps.workdir = util.Property('SCIPION_HOME')
    shortName = shortname or str(pluginName.rsplit('-', 1)[-1])  # todo: get module names more properly?
    rootName = 'scipion'
    if groupId == settings.PROD_GROUP_ID or groupId == settings.SPROD_GROUP_ID:
        scipionCmd = './scipion'
        if groupId == settings.SPROD_GROUP_ID:
            scipionCmd = './scipion3'
            rootName = 'scipion3'
        if doInstall:
            factorySteps.addStep(ShellCommand(command=[scipionCmd, 'installp', '-p', pluginName, '-j', '8'],
                                              name='Install plugin %s' % shortName,
                                              description='Install plugin %s' % shortName,
                                              descriptionDone='Installed plugin %s' % shortName,
                                              timeout=settings.timeOutInstall,
                                              haltOnFailure=True))

            if groupId == settings.PROD_GROUP_ID:
                factorySteps.addStep(ShellCommand(command=[scipionCmd, 'python', 'pyworkflow/install/inspect-plugins.py',
                                                           shortName],
                                                  name='Inspect plugin %s' % shortName,
                                                  description='Inspect plugin %s' % shortName,
                                                  descriptionDone='Inspected plugin %s' % shortName,
                                                  timeout=settings.timeOutInstall,
                                                  haltOnFailure=False))
            else:
                factorySteps.addStep(ShellCommand(command=[scipionCmd, 'inspect', shortName],
                                                 name='Inspect plugin %s' % shortName,
                                                 description='Inspect plugin %s' % shortName,
                                                 descriptionDone='Inspected plugin %s' % shortName,
                                                 timeout=settings.timeOutInstall,
                                                 haltOnFailure=False))

        if extraBinaries:
            extraBinaries = [extraBinaries] if isinstance(extraBinaries, str) else extraBinaries
            for binary in extraBinaries:
                factorySteps.addStep(ShellCommand(command=[scipionCmd, 'installb', binary, '-j', '8'],
                                                  name='Install extra package %s' % binary,
                                                  description='Install extra package  %s' % binary,
                                                  descriptionDone='Installed extra package  %s' % binary,
                                                  timeout=settings.timeOutInstall,
                                                  haltOnFailure=True))
        if doTest:
            factorySteps.addStep(
                GenerateStagesCommand(command=[scipionCmd, "test", "--show", "--grep", shortName, '--mode', 'onlyclasses'],
                                      name="Generate Scipion test stages for %s" % shortName,
                                      description="Generating Scipion test stages for %s" % shortName,
                                      descriptionDone="Generate Scipion test stages for %s" % shortName,
                                      stagePrefix=[scipionCmd, "test"],
                                      haltOnFailure=False,
                                      rootName=rootName,
                                      blacklist=settings.SCIPION_TESTS_BLACKLIST,
                                      targetTestSet=shortName))

    elif groupId == settings.SDEVEL_GROUP_ID:

        if deleteVirtualEnv:
            deleteEnv = "conda env remove --name " + deleteVirtualEnv
            removeBinCmd = " ; "
            if binToRemove:
                for binary in binToRemove:
                   removeBinCmd += "rm -rf software/em/" + binary + "* ; "

            deleteEnv += removeBinCmd
            factorySteps.addStep(ScipionCommandStep(command=deleteEnv,
                                              name='Removing the %s virtual environment' % shortName,
                                              description='Removing %s virtual environment' % shortName,
                                              descriptionDone='Removing %s virtual environment' % shortName,
                                              timeout=settings.timeOutInstall,
                                              haltOnFailure=False))

        if doInstall:
            installCmd = (settings.SCIPION_CMD + ' installp -p ' + pluginName +
                          ' -j ' + '8')

            factorySteps.addStep(ScipionCommandStep(
                command=installCmd,
                name='Install plugin %s' % shortName,
                description='Install plugin %s' % shortName,
                descriptionDone='Installed plugin %s' % shortName,
                timeout=settings.timeOutInstall,
                haltOnFailure=True))

            inspectCmd = ('python -m scipion inspect ' + shortName)

            factorySteps.addStep(ScipionCommandStep(command=inspectCmd,
                                              name='Inspect plugin %s' % shortName,
                                              description='Inspect plugin %s' % shortName,
                                              descriptionDone='Inspected plugin %s' % shortName,
                                              timeout=settings.timeOutInstall,
                                              haltOnFailure=False))

        if extraBinaries:
            for binary in extraBinaries:
                factorySteps.addStep(ScipionCommandStep(command=('%s installb %s -j 8') %(settings.SCIPION_CMD, binary),
                                                  name='Install extra package %s' % binary,
                                                  description='Install extra package  %s' % binary,
                                                  descriptionDone='Installed extra package  %s' % binary,
                                                  timeout=settings.timeOutInstall,
                                                  haltOnFailure=True))
        if doTest:
            pluginsTestShowcmd = ['bash', '-c', settings.SCIPION_ENV_ACTIVATION +
                                  ' ; ' + 'python -m scipion test --show --grep ' +
                                  shortName + ' --mode onlyclasses']

            factorySteps.addStep(
                GenerateStagesCommand(command=pluginsTestShowcmd,
                                      name="Generate Scipion test stages for %s" % shortName,
                                      description="Generating Scipion test stages for %s" % shortName,
                                      descriptionDone="Generate Scipion test stages for %s" % shortName,
                                      stagePrefix=[settings.SCIPION_CMD, "test"],
                                      haltOnFailure=False,
                                      rootName='scipion',
                                      blacklist=settings.SCIPION_TESTS_BLACKLIST,
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
    factorySteps.addStep(
        ShellCommand(command='rm -rf ' + settings.SDEVEL_DOCS_PATH,
                     name='Remove the docs folder',
                     description='Remove the docs folder',
                     descriptionDone='Remove the docs folder',
                     timeout=settings.timeOutInstall))

    docsBranch = settings.branchsDict[groupId].get(settings.DOCS_BUILD_ID, None)
    factorySteps.addStep(Git(repourl=settings.DOCS_REPO,
                             branch=docsBranch,
                             mode='incremental',
                             name='Scipion docs repository pull',
                             haltOnFailure=True))

    factorySteps.addStep(steps.SetProperty(property='SCIPION_LOCAL_CONFIG',
                                           value="~/.config/scipion/scipion_%s.conf" % groupId,
                                           name="Set SCIPION_LOCAL_CONFIG",
                                           description="Set SCIPION_LOCAL_CONFIG",
                                           descriptionDone="SCIPION_LOCAL_CONFIG set"))

    factorySteps.addStep(
        ShellCommand(command=['echo', 'SCIPION_LOCAL_CONFIG',
                              util.Property('SCIPION_LOCAL_CONFIG')],
                     name='Echo SCIPION_LOCAL_CONFIG',
                     description='Echo SCIPION_LOCAL_CONFIG',
                     descriptionDone='Echo SCIPION_LOCAL_CONFIG',
                     timeout=settings.timeOutShort
                     ))

    if groupId == settings.SDEVEL_GROUP_ID:

        # Create the pyworkflow, pwem and xmipp documentation as special cases
        command = ('sphinx-apidoc -f -e -o api/pyworkflow ' +
                   settings.SDEVEL_SCIPION_HOME + "/scipion-pyworkflow" +
                   " " + settings.SDEVEL_SCIPION_HOME + "/scipion-pyworkflow/pyworkflowtests")

        factorySteps.addStep(
            ScipionCommandStep(command=command,
                         name='Generate scipion-pyworkflow docs',
                         description='Generate scipion-pyworkflow docs',
                         descriptionDone='Generated scipion-pyworkflow docs',
                         timeout=settings.timeOutInstall))

        command = ('sphinx-apidoc -f -e -o api/pwem ' +
                   settings.SDEVEL_SCIPION_HOME + "/scipion-em" +
                   " " + settings.SDEVEL_SCIPION_HOME + "/scipion-em/pwem/tests")

        factorySteps.addStep(
            ScipionCommandStep(command=command,
                         name='Generate scipion-em docs',
                         description='Generate scipion-em docs',
                         descriptionDone='Generated scipion-em docs',
                         timeout=settings.timeOutInstall))

        command = ('sphinx-apidoc -f -e -o api/xmipp3 ' +
                   settings.SDEVEL_XMIPP_HOME + "/src/scipion-em-xmipp" +
                   " " + settings.SDEVEL_XMIPP_HOME + "/src/scipion-em-xmipp/xmipp3/tests")

        factorySteps.addStep(
            ScipionCommandStep(command=command,
                               name='Generate scipion-em-xmipp docs',
                               description='Generate scipion-em-xmipp docs',
                               descriptionDone='Generated scipion-em-xmipp docs',
                               timeout=settings.timeOutInstall))

        # Generate the plugins documentation
        plugins = {}
        plugins.update(scipionSdevelPlugins)
        plugins['scipion-em-locscale'] = {"pipName": "scipion-em-locscale",
                                          "name": "locscale",
                                          }
        for plugin, pluginDict in plugins.items():
            moduleName = str(pluginDict.get("name", plugin.rsplit('-', 1)[-1]))
            modulePath = os.path.join(settings.SCIPION_ENV_PATH, moduleName)
            if os.path.exists(modulePath):
                command = ('sphinx-apidoc -f -e -o api/' + moduleName + ' ' +
                            modulePath + ' ' + modulePath + '/tests')

                factorySteps.addStep(
                    ScipionCommandStep(command=command,
                                       name='Generate ' + moduleName + ' docs',
                                       description='Generate ' + moduleName + ' docs',
                                       descriptionDone='Generate ' + moduleName + ' docs',
                                       timeout=settings.timeOutInstall))

        # cmd = ('sphinx-versioning build -r ' + docsBranch + " " +
        #        settings.SDEVEL_DOCS_PATH + " " + settings.SDEVEL_DOCS_PATH +
        #        "/docs/_build/html")
        # factorySteps.addStep(
        #     ScipionCommandStep(command=cmd,
        #                        description='Push built docs',
        #                        name='Push built docs',
        #                        descriptionDone='Push built docs',
        #                        timeout=settings.timeOutInstall))

        cmd = 'sphinx-build . ' + settings.SDEVEL_SCIPION_HOME +'/tmp/' + docsBranch
        factorySteps.addStep(
            ScipionCommandStep(command=cmd,
                               description='Build the documentation using sphinx-build',
                               name='Build the documentation using sphinx-build in the tmp folder',
                               descriptionDone='Generated scipion-em docs',
                               timeout=settings.timeOutInstall))

        factorySteps.addStep(ShellCommand(command=["git", "add", "."],
                                          name='Git add docs',
                                          description='Git add docs',
                                          descriptionDone='Git added docs',
                                          timeout=settings.timeOutInstall))

        factorySteps.addStep(
            SetPropertyFromCommand(
                command="[[ -n $(git status -s) ]] || echo 'clean'",
                property='DOCS_REPO_STATUS_SCIPION_DOCUMENTATION',
                name='Set property DOCS_REPO_STATUS',
                description='Check repo status'))

        factorySteps.addStep(ShellCommand(
            command=["git", "commit", "-m", "buildbot automated-update"],
            name='Git commit the builded docs',
            description='Git commit the builded docs',
            descriptionDone='Git commit the builded docs',
            doStepIf=doCommit,
            timeout=settings.timeOutInstall))

        factorySteps.addStep(
            ShellCommand(command='git checkout gh-pages',
                         name='Checkout to gh_pages branch in order to copy the builded documentation',
                         description='Checkout to gh_pages branch in order to copy the builded documentation',
                         descriptionDone='Checkout to gh_pages branch in order to copy the builded documentation',
                         timeout=settings.timeOutInstall))
        factorySteps.addStep(
            ShellCommand(command='git pull',
                         name='Integrate the remote changes',
                         description='Integrate the remote changes',
                         descriptionDone='Integrate the remote changes',
                         timeout=settings.timeOutInstall))

        factorySteps.addStep(
            ShellCommand(command='cp -r ' + settings.SDEVEL_SCIPION_HOME +
                                 '/tmp/' + docsBranch + ' .',
                         name='Update the API documentation',
                         description='Update the API documentation',
                         descriptionDone='Update the API documentation',
                         timeout=settings.timeOutInstall))

        factorySteps.addStep(
            ShellCommand(command='rm -rf ' + settings.SDEVEL_SCIPION_HOME +
                                 '/tmp/',
                         name='Delete the tmp folder',
                         description='Delete the tmp folder',
                         descriptionDone='Delete the tmp folder',
                         timeout=settings.timeOutInstall))

        factorySteps.addStep(ShellCommand(command=["git", "add", "."],
                                          name='Git add docs',
                                          description='Git add docs',
                                          descriptionDone='Git added docs',
                                          timeout=settings.timeOutInstall))

        factorySteps.addStep(
            SetPropertyFromCommand(
                command="[[ -n $(git status -s) ]] || echo 'clean'",
                property='DOCS_REPO_STATUS_API_DOCUMENTATION',
                name='Set property DOCS_REPO_STATUS',
                description='Check repo status'))

        factorySteps.addStep(ShellCommand(
            command=["git", "commit", "-m", "buildbot automated-update"],
            name='Git commit the builded docs',
            description='Git commit the builded docs',
            descriptionDone='Git commit the builded docs',
            doStepIf=doCommit,
            timeout=settings.timeOutInstall))

        factorySteps.addStep(ShellCommand(command=["git", "push"],
                                          name='Git push the builded docs to repo',
                                          description='Git push the builded docs to repo',
                                          descriptionDone='Git push the builded docs to repo',
                                          timeout=settings.timeOutInstall))
        factorySteps.addStep(
            ShellCommand(command='git checkout ' + docsBranch,
                         name='Checkout to ' + docsBranch + ' branch',
                         description='Checkout to ' + docsBranch + ' branch',
                         descriptionDone='Checkout to ' + docsBranch + ' branch',
                         timeout=settings.timeOutInstall))

    else:
        command = ['sphinx-apidoc', '-f', '-e', '-o', 'api/',
                   util.Interpolate("%(prop:SCIPION_HOME)s/pyworkflow"),
                   util.Interpolate("%(prop:SCIPION_HOME)s/pyworkflow/tests/*")]

        factorySteps.addStep(
            ShellCommand(command=command,
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
        if groupId != settings.SDEVEL_GROUP_ID:
            factorySteps.addStep(ShellCommand(
                command=[util.Interpolate("%(prop:SCIPION_HOME)s/scipion"),
                         "run", util.Property('sphinx-versioning'), 'push', '-r',
                         docsBranch,
                         util.Property('DOCS_HOME'), settings.DOCS_HTML_BRANCH,
                         "."],
                name='Push built docs',
                description='Pushing built docs',
                descriptionDone='Pushed built docs',
                timeout=settings.timeOutInstall))
        else:
            cmd = ('sphinx-versioning push -r ' + docsBranch + " " +
                   settings.SDEVEL_DOCS_PATH + " " + settings.DOCS_HTML_BRANCH +
                   " .")
            factorySteps.addStep(
                ScipionCommandStep(command=cmd,
                                   description='Push built docs',
                                   name='Push built docs',
                                   descriptionDone='Push built docs',
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
                         factory=pluginFactory(groupId, 'scipion-em-locscale', factorySteps=builderFactory),
                         workerbuilddir=groupId,
                         properties={'slackChannel': locscalePluginData.get('slackChannel', "")},
                         env=locscaleEnv)


def getScipionBuilders(groupId):
    scipionBuilders = []
    env = {"SCIPION_IGNORE_PYTHONPATH": "True",
           "SCIPION_LOCAL_CONFIG": util.Property('SCIPION_LOCAL_CONFIG'),
           "LD_LIBRARY_PATH": settings.LD_LIBRARY_PATH}

    if groupId == settings.PROD_GROUP_ID:

        scipionBuilders.append(
            BuilderConfig(name=settings.SCIPION_INSTALL_PREFIX + groupId,
                          tags=[groupId],
                          workernames=[settings.WORKER],
                          factory=installScipionFactory(groupId),
                          workerbuilddir=groupId,
                          properties={"slackChannel": settings.SCIPION_SLACK_CHANNEL},
                          env=env)
        )
        scipionBuilders.append(
            BuilderConfig(name=settings.SCIPION_TESTS_PREFIX + groupId,
                          tags=[groupId],
                          workernames=[settings.WORKER],
                          factory=scipionTestFactory(groupId),
                          workerbuilddir=groupId,
                          properties={'slackChannel': settings.SCIPION_SLACK_CHANNEL},
                          env=env)
        )

        scipionBuilders.append(
            BuilderConfig(name=settings.CLEANUP_PREFIX + groupId,
                          tags=[groupId],
                          workernames=[settings.WORKER],
                          factory=cleanUpFactory(),
                          workerbuilddir=groupId,
                          properties={'slackChannel': settings.SCIPION_SLACK_CHANNEL},
                          env=env)
        )

        # special locscale case, we need to install eman212

        for plugin, pluginDict in scipionPlugins.items():
            moduleName = str(pluginDict.get("name", plugin.rsplit('-', 1)[-1]))
            tags = [groupId, moduleName]
            hastests = not pluginDict.get("NO_TESTS", False)
            scipionBuilders.append(
                BuilderConfig(name="%s_%s" % (moduleName, groupId),
                              tags=tags,
                              workernames=[settings.WORKER],
                              factory=pluginFactory(groupId, plugin, shortname=moduleName, doTest=hastests),
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
    elif groupId == settings.SDEVEL_GROUP_ID or groupId == settings.SPROD_GROUP_ID:

        if groupId == settings.SDEVEL_GROUP_ID:
            env['SCIPION_HOME'] = settings.SDEVEL_SCIPION_HOME
            env['EM_ROOT'] = settings.EM_ROOT
            env['LD_LIBRARY_PATH'] = settings.LD_LIBRARY_PATH
            scipionBuilders.append(
                BuilderConfig(name=settings.SCIPION_INSTALL_PREFIX + groupId,
                              tags=[groupId],
                              workernames=[settings.WORKER],
                              factory=installSDevelScipionFactory(groupId),
                              workerbuilddir=groupId,
                              properties={
                                  "slackChannel": settings.SCIPION_SLACK_CHANNEL},
                              env=env))
        else:
            env['SCIPION_HOME'] = settings.SPROD_SCIPION_HOME
            env['EM_ROOT'] = settings.SPROD_EM_ROOT
            env['LD_LIBRARY_PATH'] = settings.PROD_LD_LIBRARY_PATH
            env['PATH'] = ["/usr/local/cuda/bin", "${PATH}"]
            scipionBuilders.append(
                BuilderConfig(name=settings.SCIPION_INSTALL_PREFIX + groupId,
                              tags=[groupId],
                              workernames=[settings.WORKER],
                              factory=installProdScipionFactory(groupId),
                              workerbuilddir=groupId,
                              properties={
                                  "slackChannel": settings.SCIPION_SLACK_CHANNEL},
                              env=env))
        scipionBuilders.append(
            BuilderConfig(name=settings.SCIPION_TESTS_PREFIX + groupId,
                          tags=[groupId],
                          workernames=[settings.WORKER],
                          factory=scipionTestFactory(groupId),
                          workerbuilddir=groupId,
                          properties={
                              'slackChannel': settings.SCIPION_SLACK_CHANNEL},
                          env=env)
        )
        if groupId == settings.SDEVEL_GROUP_ID:
            env['SCIPION_PLUGIN_JSON'] = 'plugins.json'
            scipionBuilders.append(
                BuilderConfig(name=settings.CLEANUP_PREFIX + groupId,
                              tags=[groupId],
                              workernames=[settings.WORKER],
                              factory=cleanUpFactory(rmXmipp=True),
                              workerbuilddir=groupId,
                              properties={
                                  'slackChannel': settings.SCIPION_SLACK_CHANNEL},
                              env=env)
            )
        else:
            scipionBuilders.append(
                BuilderConfig(name=settings.CLEANUP_PREFIX + groupId,
                              tags=[groupId],
                              workernames=[settings.WORKER],
                              factory=cleanUpFactory(),
                              workerbuilddir=groupId,
                              properties={
                                  'slackChannel': settings.SCIPION_SLACK_CHANNEL},
                              env=env)
            )

        for plugin, pluginDict in scipionSdevelPlugins.items():
            moduleName = str(pluginDict.get("name", plugin.rsplit('-', 1)[-1]))
            tags = [groupId, moduleName]
            hastests = not pluginDict.get("NO_TESTS", False)
            extraBinaries = pluginDict.get("extraBinaries", [])
            deleteVirtualEnv = pluginDict.get("deleteVirtualEnv", '')
            binToRemove = pluginDict.get("binToRemove", [])
            scipionBuilders.append(
                BuilderConfig(name="%s_%s" % (moduleName, groupId),
                              tags=tags,
                              workernames=[settings.WORKER],
                              factory=pluginFactory(groupId, plugin,
                                                    shortname=moduleName,
                                                    doTest=hastests,
                                                    extraBinaries=extraBinaries,
                                                    deleteVirtualEnv=deleteVirtualEnv,
                                                    binToRemove=binToRemove),
                              workerbuilddir=groupId,
                              properties={'slackChannel': scipionSdevelPlugins[plugin].get('slackChannel', "")},
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
        scipionBuilders.append(
            BuilderConfig(name="%s%s" % (settings.WEBSITE_PREFIX, groupId),
                          tags=["web", groupId],
                          workernames=[settings.WORKER],
                          factory=updateWebSite(groupId),
                          workerbuilddir=groupId,
                          properties={
                              'slackChannel': "buildbot"},
                          env=env))

    return scipionBuilders


# #############################################################################
# ############################## SCHEDULERS ###################################
# #############################################################################

def updateWebSite(groupId):
    updateWebFactorySteps = util.BuildFactory()
    updateWebFactorySteps.workdir = settings.SCIPION_BUILD_ID

    updateWebFactorySteps.addStep(
        ScipionCommandStep(command=updateWebSiteCmd,
                           name='Update the Scipion web site',
                           description='Update the Scipion web site',
                           descriptionDone='Update the Scipion web site',
                           timeout=settings.timeOutInstall,
                           haltOnFailure=True))
    return updateWebFactorySteps


def getScipionSchedulers(groupId):
    if groupId == settings.SDEVEL_GROUP_ID or groupId == settings.SPROD_GROUP_ID:
        scipionSchedulerNames = [settings.SCIPION_INSTALL_PREFIX + groupId,
                                 settings.SCIPION_TESTS_PREFIX + groupId,
                                 settings.CLEANUP_PREFIX + groupId]

        if settings.branchsDict[groupId].get(settings.DOCS_BUILD_ID, None) is not None:
            scipionSchedulerNames.append("%s%s" % (settings.DOCS_PREFIX, groupId))

        scipionSchedulerNames.append("%s%s" % (settings.WEBSITE_PREFIX, groupId))

        schedulers = []
        for name in scipionSchedulerNames:
            schedulers.append(triggerable.Triggerable(name=name,
                                                      builderNames=[name]))
            schedulers.append(
                ForceScheduler(name='%s%s' % (settings.FORCE_BUILDER_PREFIX, name),
                               builderNames=[name]))

        plugins = {}
        plugins.update(scipionSdevelPlugins)
        plugins.update({"scipion-em-locscale": locscaleSdevelPluginData})
        for plugin, pluginDict in plugins.items():
            moduleName = str(pluginDict.get("name", plugin.rsplit('-', 1)[-1]))
            schedulers.append(
                triggerable.Triggerable(name="%s_%s" % (moduleName, groupId),
                                        builderNames=[
                                            "%s_%s" % (moduleName, groupId)]))

            forceSchedulerName = '%s%s_%s' % (
            settings.FORCE_BUILDER_PREFIX, moduleName, groupId)
            schedulers.append(
                ForceScheduler(name=forceSchedulerName,
                               builderNames=["%s_%s" % (moduleName, groupId)]))

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
        for plugin, pluginDict in plugins.items():
            moduleName = str(pluginDict.get("name", plugin.rsplit('-', 1)[-1]))
            schedulers.append(triggerable.Triggerable(name="%s_%s" % (moduleName, groupId),
                                                      builderNames=["%s_%s" % (moduleName, groupId)]))

            forceSchedulerName = '%s%s_%s' % (settings.FORCE_BUILDER_PREFIX, moduleName, groupId)
            schedulers.append(
                ForceScheduler(name=forceSchedulerName,
                               builderNames=["%s_%s" % (moduleName, groupId)]))

    return schedulers
