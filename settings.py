from buildbot.plugins import util
import os

################## buildbot ##################
#  worker credentials
WORKER = os.environ.get('BUILDBOT_WORKER')
WORKER_PASS = os.environ.get("BUILDBOT_WORKER_PASS")
PORT = 9989

# Website settings
WEB_PORT = 9980
WEB_URL = 'http://arquimedes.cnb.csic.es:9980/'

# builder timeouts
timeOutInstall = 3600  # 1 hour
timeOutExecute = 36000  # 10 hours
timeOutLongExecute = 72000  # 20 hours

# builder branches
DEVEL_GROUP_ID = 'devel'
PROD_GROUP_ID = 'prod'
SCIPION_BUILD_ID = 'scipion'  # this will be the name of the builder dir i.e. the scipion home
XMIPP_BUILD_ID = 'xmipp'  # this will be the dir name of xmipp's home
FORCE_BUILDER_PREFIX = 'Force_'


# Here we define the structure of the builders. For each build group (prod and devel up to now)
# we can define the branches of scipion and xmipp that we want to test. The branches of the
# plugins are defined in plugins.json (e.g. using a pluginSourceUrl that points to the specific branch).
# Buildbot will have one "orchestrator" builder for each build group, which will be in charge of
# triggering the installation and testing stages of scipion, xmipp and each plugin.
branchsDict = {DEVEL_GROUP_ID: {SCIPION_BUILD_ID: 'add_queuestepexecutor',
                                XMIPP_BUILD_ID: 'devel'},
               PROD_GROUP_ID: {
                   SCIPION_BUILD_ID: 'devel-pluginization'
               }}

################## Scipion settings ##################

# vars in scipion.conf
MPI_LIBDIR = "/usr/lib/x86_64-linux-gnu/openmpi/lib"
MPI_INCLUDE = "/usr/lib/x86_64-linux-gnu/openmpi/include"
MPI_BINDIR = "/usr/bin"
CUDA_LIB = "/usr/local/cuda-8.0/lib64"
CCP4_HOME = "/opt/ccp4-7.0"
PHENIX_HOME = "/usr/local/phenix-1.13-2998/"

# data for the builders
PLUGINS_JSON_FILE = "getplugins.json"
EMAN212 = {"EMAN2DIR": util.Interpolate("%(prop:SCIPION_HOME)s/software/em/eman-2.12")}
gitRepoURL = 'https://github.com/I2PC/scipion.git'

# builder prefixes
SCIPION_INSTALL_PREFIX = 'Install_Scipion_'
SCIPION_TESTS_PREFIX = 'Test_Scipion_'
CLEANUP_PREFIX = 'CleanUp_'

# slack channel
SCIPION_SLACK_CHANNEL = "buildbot"

################### Xmipp settings ##################
XMIPP_SCRIPT_URL = "https://raw.githubusercontent.com/I2PC/xmipp/devel/xmipp"
# builder prefixes
XMIPP_INSTALL_PREFIX = 'Install_Xmipp_'
XMIPP_TESTS = 'xmipp_'
XMIPP_BUNDLE_TESTS = 'xmipp_bundle_'
# slack channel
XMIPP_SLACK_CHANNEL = "xmipp"

# xmipp.conf variables
CUDA = 'True'
NVCC = 'nvcc'
NVCC_CXXFLAGS = "--x cu -D_FORCE_INLINES -Xcompiler -fPIC -Wno-deprecated-gpu-targets -ccbin g++-5"
NVCC_LINKFLAGS = '-L/usr/local/cuda/lib64'

