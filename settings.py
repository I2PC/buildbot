from buildbot.plugins import util
import os


# Local settings
try:
    from localsettings import *
except ImportError:
    print("WARNING: local settings not found, using default values.")
    ################## buildbot ##################
    #  worker credentials
    WORKER = os.environ.get('BUILDBOT_WORKER', 'worker')
    WORKER_PASS = os.environ.get("BUILDBOT_WORKER_PASS", "password")
    PORT = 9989

    # Website settings
    WEB_PORT = 9980
    WEB_URL = 'http://scipion-test.cnb.csic.es:9980/'

    # builder timeouts
    timeOutShort = 5*60  # 5 minutes
    timeOutInstall = 60*60  # 1 hour
    timeOutExecute = 5*60*60  # 5 hours
    timeOutLongExecute = 20*60*60  # 20 hours

    # builder branches
    DEVEL_GROUP_ID = 'devel'
    PROD_GROUP_ID = 'prod'
    SDEVEL_GROUP_ID = 'sdevel'

    SCIPION_BUILD_ID = 'scipion'  # this will be the name of the builder dir i.e. the scipion home
    XMIPP_BUILD_ID = 'xmipp'  # this will be the dir name of xmipp's home
    DOCS_BUILD_ID = 'docs'
    NYSBC_BUILD_ID = 'nysbc'
    FORCE_BUILDER_PREFIX = 'Force_'

    SCIPION_APP_BUILD_ID = 'scipion-app'
    SCIPION_PYWORKFLOW_BUILD_ID = 'scipion-pyworkflow'
    SCIPION_EM_BUILD_ID = 'scipion-em'

    # Here we define the structure of the builders. For each build group (prod and devel up to now)
    # we can define the branches of scipion and xmipp that we want to test. The branches of the
    # plugins are defined in plugins.json (e.g. using a pluginSourceUrl that points to the specific branch).
    # Buildbot will have one "orchestrator" builder for each build group, which will be in charge of
    # triggering the installation and testing stages of scipion, xmipp and each plugin.
    branchsDict = {DEVEL_GROUP_ID: {SCIPION_BUILD_ID: 'devel',
                                    XMIPP_BUILD_ID: 'devel',
                                    DOCS_BUILD_ID: 'release-2.0.0'},
                   PROD_GROUP_ID: {
                       SCIPION_BUILD_ID: 'master'
                   },
                   SDEVEL_GROUP_ID: {
                       SCIPION_APP_BUILD_ID: 'devel-fixes',
                       SCIPION_EM_BUILD_ID: 'devel',
                       SCIPION_PYWORKFLOW_BUILD_ID: 'devel-fixes',
                       XMIPP_BUILD_ID: 'python3_migration'

                   }}

    ################## Scipion settings ##################

    # vars in scipion.conf
    MPI_LIBDIR = "/usr/lib/x86_64-linux-gnu/openmpi/lib"
    MPI_INCLUDE = "/usr/lib/x86_64-linux-gnu/openmpi/include"
    MPI_BINDIR = "/usr/bin"
    CUDA = "True"
    CUDA_LIB = "/usr/local/cuda-8.0/lib64"
    CCP4_HOME = "/opt/ccp4-7.0"
    PHENIX_HOME = "/usr/local/phenix-1.13-2998"
    CONDA_ACTIVATION_CMD = ". /home/buildbot/miniconda3/etc/profile.d/conda.sh;"
    SDEVEL_SCIPION_HOME = '/home/buildbot/sdevel/scipion'
    SDEVEL_XMIPP_HOME = '/home/buildbot/sdevel/xmipp'
    BUILDBOT_HOME = '/home/buildbot/'
    NYSBC_3DFSC_HOME = SDEVEL_SCIPION_HOME + "/software/em/nysbc3DFSC-2.5"
    CRYOLO_NS_GENERIC_MODEL = SDEVEL_SCIPION_HOME + "/software/em/cryolo_model-201910/gmodel_phosnet_201910.h5"
    CRYOLO_ENV_ACTIVATION = ". /home/buildbot/miniconda3/etc/profile.d/conda.sh; conda activate cryolo-1.5.4"

    # Cryosparc variables
    # The root directory where cryoSPARC code and dependencies is installed.
    CRYOSPARC_DIR = "/home/buildbot/cryosparc/"

    # full name of the initial admin account to be created
    CRYOSPARC_USER = "Yunior C. Fonseca Reyna"

    # data for the builders
    PLUGINS_JSON_FILE = "getplugins.json"

    # data for the sdevel builders
    SDEVELPLUGINS_JSON_FILE = "getsdevelplugins.json"

    #So far, what is in prod has to work with EMAN2.12
    EMAN212 = {"EMAN2DIR": util.Interpolate("%(prop:SCIPION_HOME)s/software/em/eman-2.12")}
    # Eman plugin in devel installs 2.3 ans is compatible with locscale
    EMAN23 = {"EMAN2DIR": util.Interpolate("%(prop:SCIPION_HOME)s/software/em/eman-23")}
    gitRepoURL = 'https://github.com/I2PC/scipion.git'
    DOCS_REPO = "git@github.com:scipion-em/docs.git"
    DOCS_HTML_BRANCH = 'gh-pages'

    #New verion of Scipion
    sdevel_gitRepoURL = ("-b %s https://github.com/scipion-em/scipion-app.git"
                        % branchsDict[SDEVEL_GROUP_ID].get(SCIPION_APP_BUILD_ID, "devel"))

    sdevel_pw_gitRepoURL = ("-b %s https://github.com/scipion-em/scipion-pyworkflow.git"
                        % branchsDict[SDEVEL_GROUP_ID].get(SCIPION_PYWORKFLOW_BUILD_ID, "devel"))

    sdevel_pyem_gitRepoURL = ("-b %s https://github.com/scipion-em/scipion-em.git"
                        % branchsDict[SDEVEL_GROUP_ID].get(SCIPION_EM_BUILD_ID, "devel"))

    sdevelXmipp_gitRepoURL = ("-b %s https://github.com/I2PC/scipion-em-xmipp.git"
                         % branchsDict[SDEVEL_GROUP_ID].get(XMIPP_BUILD_ID, "devel"))


    SCIPION_ENV_ACTIVATION = "source /home/buildbot/miniconda3/etc/profile.d/conda.sh ; conda activate scipion_python3"
    SCIPION_CMD = "python -m scipion"

    # builder prefixes
    SCIPION_INSTALL_PREFIX = 'Install_Scipion_'
    SCIPION_TESTS_PREFIX = 'Test_Scipion_'
    CLEANUP_PREFIX = 'CleanUp_'
    DOCS_PREFIX = "docs_"
    WEBSITE_PREFIX = "Update_scipion_web_site_"

    # slack channel
    SCIPION_SLACK_CHANNEL = "buildbot"

    # List of the lengthy tests so that we put them at the end.
    SCIPION_LONG_TESTS = ["pyworkflow.tests.em.workflows.test_workflow_mixed_large.TestMixedRelionTutorial",
                          "pyworkflow.tests.em.workflows.test_workflow_mixed_large.TestMixedFrealignClassify",
                          "pyworkflow.tests.em.workflows.test_workflow_modeling.TestMolprobityValidation",
                          "pyworkflow.tests.em.workflows.test_workflow_initialvolume.TestRibosome",
                          "pyworkflow.tests.em.workflows.test_workflow_initialvolume.TestBPV",
                          "pyworkflow.tests.em.workflows.test_workflow_xmipp_rct.TestXmippRCTWorkflow",
                          ]

    # Scipion test blacklist - these wont be executed with the rest of pyworkflow tests
    SCIPION_TESTS_BLACKLIST = (SCIPION_LONG_TESTS +
                               ["pyworkflow.tests.em.workflows.test_parallel_gpu_queue.TestNoQueueSmall",
                                "pyworkflow.tests.em.workflows.test_parallel_gpu_queue.TestNoQueueALL",
                                "pyworkflow.tests.em.workflows.test_parallel_gpu_queue.TestQueueSmall",
                                "pyworkflow.tests.em.workflows.test_parallel_gpu_queue.TestQueueALL",
                                "pyworkflow.tests.em.workflows.test_parallel_gpu_queue.TestQueueSteps",
                                "pyworkflow.tests.em.workflows.test_workflow_existing.TestXmippWorkflow"])

    ################### Xmipp settings ##################
    XMIPP_REPO_URL = ("-b %s https://github.com/I2PC/xmipp.git"
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
