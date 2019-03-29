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
DOCS_BUILD_ID = 'docs'
FORCE_BUILDER_PREFIX = 'Force_'

# Here we define the structure of the builders. For each build group (prod and devel up to now)
# we can define the branches of scipion and xmipp that we want to test. The branches of the
# plugins are defined in plugins.json (e.g. using a pluginSourceUrl that points to the specific branch).
# Buildbot will have one "orchestrator" builder for each build group, which will be in charge of
# triggering the installation and testing stages of scipion, xmipp and each plugin.
branchsDict = {DEVEL_GROUP_ID: {SCIPION_BUILD_ID: 'release-2.0.0-fixes',
                                XMIPP_BUILD_ID: 'release-19.03-fixes',
                                DOCS_BUILD_ID: 'release-2.0.0'},
               PROD_GROUP_ID: {
                   SCIPION_BUILD_ID: 'release-2.0.0-fixes'
               }}

################## Scipion settings ##################

# vars in scipion.conf
MPI_LIBDIR = "/usr/lib/x86_64-linux-gnu/openmpi/lib"
MPI_INCLUDE = "/usr/lib/x86_64-linux-gnu/openmpi/include"
MPI_BINDIR = "/usr/bin"
CUDA_LIB = "/usr/local/cuda-8.0/lib64"
CCP4_HOME = "/opt/ccp4-7.0"
PHENIX_HOME = "/usr/local/phenix-1.13-2998"

# data for the builders
PLUGINS_JSON_FILE = "getplugins.json"
EMAN212 = {"EMAN2DIR": util.Interpolate("%(prop:SCIPION_HOME)s/software/em/eman-2.12")}
gitRepoURL = 'https://github.com/I2PC/scipion.git'
DOCS_REPO = "git@github.com:scipion-em/docs.git"
DOCS_HTML_BRANCH = 'gh-pages'


# builder prefixes
SCIPION_INSTALL_PREFIX = 'Install_Scipion_'
SCIPION_TESTS_PREFIX = 'Test_Scipion_'
CLEANUP_PREFIX = 'CleanUp_'
DOCS_PREFIX = "docs_"

# slack channel
SCIPION_SLACK_CHANNEL = "buildbot"

# Scipion test blacklist
SCIPION_TESTS_BLACKLIST = ["pyworkflow.tests.em.workflows.test_parallel_gpu_queue.TestNoQueueSmall",
                           "pyworkflow.tests.em.workflows.test_parallel_gpu_queue.TestNoQueueALL",
                           "pyworkflow.tests.em.workflows.test_parallel_gpu_queue.TestQueueSmall",
                           "pyworkflow.tests.em.workflows.test_parallel_gpu_queue.TestQueueALL",
                           "pyworkflow.tests.em.workflows.test_parallel_gpu_queue.TestQueueSteps",
                           "pyworkflow.tests.em.workflows.test_workflow_existing.TestXmippWorkflow"]

################### Xmipp settings ##################
XMIPP_SCRIPT_URL = ("https://raw.githubusercontent.com/I2PC/xmipp/%s/xmipp"
                    % branchsDict[DEVEL_GROUP_ID].get(XMIPP_BUILD_ID, "devel"))
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
LD_LIBRARY_PATH = '/usr/local/cuda-8.0/lib64'
XMIPP_BUNDLE_VARS = ["LD_LIBRARY_PATH", "PATH", "PYTHONPATH",
                     "XMIPP_HOME", "XMIPP_SRC"]
