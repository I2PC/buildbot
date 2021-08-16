from buildbot.plugins import util
import os


# Local settings
try:
    from localsettings import *
except ImportError:
    print("WARNING: local settings not found, using default values.")
    ################## buildbot ##################
    #  worker credentials
    WORKER = os.environ.get('BUILDBOT_WORKER', 'einstein')
    WORKER1 = os.environ.get('BUILDBOT_WORKER1', 'scipionbox')
    WORKER_PASS = os.environ.get("BUILDBOT_WORKER_PASS", "password")
    PORT = 9989

    # Website settings
    WEB_PORT = 9980
    WEB_URL = 'http://scipion-test.cnb.csic.es:9980/'

    SCIPION_SITE_URL = 'http://scipion.i2pc.es/'

    # builder timeouts
    timeOutShort = 5*60  # 5 minutes
    timeOutInstall = 60*60  # 1 hour
    timeOutExecute = 5*60*60  # 5 hours
    timeOutLongExecute = 20*60*60  # 20 hours

    # builder branches
    PROD_GROUP_ID = 'support'
    SDEVEL_GROUP_ID = 'devel'
    SPROD_GROUP_ID = 'prod'

    SCIPION_BUILD_ID = 'scipion'  # this will be the name of the builder dir i.e. the scipion home
    XMIPP_BUILD_ID = 'xmipp'  # this will be the dir name of xmipp's home
    DOCS_BUILD_ID = 'docs'
    XMIPP_DOCS_BUILD_ID = 'xmippDoc'
    XMIPP_JAR_DOCS_BUILD_ID = 'xmippJavaDoc'
    XMIPP_PY_DOCS_BUILD_ID = 'xmippPythonDoc'
    NYSBC_BUILD_ID = 'nysbc'
    FORCE_BUILDER_PREFIX = 'Force_'

    SCIPION_APP_BUILD_ID = 'scipion-app'
    SCIPION_PYWORKFLOW_BUILD_ID = 'scipion-pyworkflow'
    SCIPION_EM_BUILD_ID = 'scipion-em'

    # Number of lines to show in the log file
    PROT_LOGS_LAST_LINES = "100"

    # Here we define the structure of the builders. For each build group (prod and devel up to now)
    # we can define the branches of scipion and xmipp that we want to test. The branches of the
    # plugins are defined in plugins.json (e.g. using a pluginSourceUrl that points to the specific branch).
    # Buildbot will have one "orchestrator" builder for each build group, which will be in charge of
    # triggering the installation and testing stages of scipion, xmipp and each plugin.
    branchsDict = {PROD_GROUP_ID: {
                       SCIPION_BUILD_ID: 'master'
                   },
                   SDEVEL_GROUP_ID: {
                       SCIPION_BUILD_ID: 'devel',
                       DOCS_BUILD_ID: 'release-3.0.0',
                       XMIPP_DOCS_BUILD_ID: 'gh-pages'

                   },
                    SPROD_GROUP_ID: {
                        SCIPION_BUILD_ID: 'master',
                    }}

    ################## Scipion settings ##################

    # vars in scipion.conf
    EM_ROOT = "/home/buildbot/devel/scipion/software/em"
    SPROD_EM_ROOT = "/home/buildbot/prod/scipion/software/em"
    MPI_LIBDIR = "/usr/lib/x86_64-linux-gnu/openmpi/lib"
    MPI_INCLUDE = "/usr/lib/x86_64-linux-gnu/openmpi/include"
    MPI_BINDIR = "/usr/bin"
    CUDA_LIB = "/usr/local/cuda-10.2/lib64"
    MOTIONCOR2_CUDA_LIB_SUPPORT = "/usr/local/cuda-8.0/lib64"
    MOTIONCOR2_BIN_SUPPORT = 'MotionCor2_1.3.0-Cuda80'
    MOTIONCOR2_CUDA_LIB = "/usr/local/cuda-10.2/lib64"
    MOTIONCOR2_BIN = 'MotionCor2_1.3.2-Cuda102'
    MOTIONCOR2_BIN_DEVEL = 'MotionCor2_1.4.0_Cuda102'
    GCTF = 'Gctf_v1.18_sm30-75_cu10.1'
    GCTF_CUDA_LIB = '/usr/local/cuda-10.2/lib64'
    GAUTOMATCH = 'Gautomatch_v0.56_sm30-75_cu10.1'
    GAUTOMATCH_CUDA_LIB = "/usr/local/cuda-10.2/lib64"
    SPIDER = 'spider_linux_mp_intel64'
    SPIDER_MPI = 'spider_linux_mpi_opt64'
    CCP4_HOME = "/opt/xtal/ccp4-7.1"
    PHENIX_HOME = "/usr/local/phenix-1.19.1-4122"
    CONDA_ACTIVATION_CMD = ". /home/buildbot/miniconda3/etc/profile.d/conda.sh"
    CONDA_ACTIVATION_CMD_DEVEL = ". /home/buildbot/anaconda3/etc/profile.d/conda.sh"
    aphinxENV_ACTIVATE = CONDA_ACTIVATION_CMD + " && . ~/.sphinxVenv/bin/activate"
    CONDA_REMOVE_DEVEL_ENV = "conda env remove -n develEnv"
    DEVEL_ENV = "develEnv"
    PROD_ENV = "prodEnv"
    DEVEL_ENV_ACTIVATION = CONDA_ACTIVATION_CMD_DEVEL + " && conda activate " + DEVEL_ENV
    PROD_ENV_ACTIVATION = CONDA_ACTIVATION_CMD + " && conda activate " + PROD_ENV
    CONDA_REMOVE_PROD_ENV = "conda env remove -n prodEnv"
    SDEVEL_SCIPION_HOME = '/home/buildbot/devel/scipion'
    SPROD_SCIPION_HOME = '/home/buildbot/prod/scipion'
    SPROD_ENV_PATH = '/home/buildbot/prod/condaenvs/prodEnv'
    SDEVEL_ENV_PATH = '/home/buildbot/anaconda3/envs/develEnv'
    SDEVEL_XMIPP_HOME = '/home/buildbot/devel/scipion/xmipp-bundle'
    SPROD_XMIPP_HOME = '/home/buildbot/prod/scipion/xmipp-bundle'
    BUILDBOT_HOME = '/home/buildbot/'
    NYSBC_3DFSC_HOME = SDEVEL_SCIPION_HOME + "/software/em/fsc3D-3.0"
    CRYOLO_NS_GENERIC_MODEL = SDEVEL_SCIPION_HOME + "/software/em/cryolo_model-202002_N63/gmodel_phosnet_202002_N63.h5"
    CRYOLO_ENV_ACTIVATION = ". /home/buildbot/miniconda3/etc/profile.d/conda.sh; conda activate cryolo-1.6.1"
    CRYOLO_CUDA_LIB = "/usr/local/cuda-10.2/lib64"
    RELION_CUDA_LIB = "/usr/local/cuda-10.2/lib64"
    RELION_CUDA_BIN = "/usr/local/cuda-10.2/bin"
    CHIMERA_HOME = "/home/buildbot/chimerax-1.1"
    EMAN2_HOME = os.path.join(EM_ROOT, 'eman-3.0.0-alpha')
    JJSOFT_HOME = "/home/buildbot/jjsoft"
    BUILD_TESTS = "True"

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
    EMAN23 = {"EMAN2DIR": util.Interpolate("%(prop:SCIPION_HOME)s/software/em/eman-2.3")}
    gitRepoURL = 'https://github.com/I2PC/scipion.git'
    DOCS_REPO = "git@github.com:scipion-em/docs.git"
    DOCS_HTML_BRANCH = 'gh-pages'
    DOCS_HOME = "/home/buildbot/scipionBot/devel/docs"
    SDEVEL_DOCS_PATH = "/home/buildbot/devel/docs"
    SDEVEL_DOCS_API_PATH = SDEVEL_DOCS_PATH + "/api"

    SCIPION_CMD = "./scipion3"
    SCIPION_PYTHON_CMD = './scipion3 python'
    PROD_SCIPION_CMD = "./scipion3"
    XMIPP_CMD = "./xmipp"
    SCIPION_ENV_PATH = "/home/buildbot/.conda/envs/scipion_python3/lib/python3.5/site-packages/"
    SCIPION_SDEVEL_ENV_PATH = SDEVEL_ENV_PATH + "/lib/python3.8/site-packages/"

    SDEVEL_SCIPION_CONFIG_PATH = "/home/buildbot/.config/scipion/scipion_devel.conf"
    SPROD_SCIPION_CONFIG_PATH = "/home/buildbot/.config/scipion/scipion_prod.conf"

    # SCIPION SCRATCH DIR
    SCIPION_SCRATCH = "/home/buildbot/scratch"

    # CODESPEED_URL
    CODESPEED_URL = "http://scipion-test.cnb.csic.es:8000"
    CODESPEED_ENV = "einstein"
    PROFILING_PROJECTS_PATH = "/home/buildbot/scipionBot/profilingProjects/"

    # builder prefixes
    SCIPION_INSTALL_PREFIX = 'Install_Scipion_'
    SCIPION_TESTS_PREFIX = 'Test_Scipion_'
    CLEANUP_PREFIX = 'CleanUp_'
    DOCS_PREFIX = "docs_"
    WEBSITE_PREFIX = "Update_scipion_web_site_"
    CHECK_PLUGINS_DIFF = 'Check_plugins_diff_'

    # slack channel
    SCIPION_SLACK_CHANNEL = "buildbot"

    # List of the lengthy tests so that we put them at the end.
    SCIPION_LONG_TESTS = ["pyworkflow.tests.em.workflows.test_workflow_mixed_large.TestMixedRelionTutorial",
                          "pyworkflow.tests.em.workflows.test_workflow_mixed_large.TestMixedFrealignClassify",
                          "pyworkflow.tests.em.workflows.test_workflow_modeling.TestMolprobityValidation",
                          "pyworkflow.tests.em.workflows.test_workflow_initialvolume.TestRibosome",
                          "pyworkflow.tests.em.workflows.test_workflow_initialvolume.TestBPV",
                          "pyworkflow.tests.em.workflows.test_workflow_xmipp_rct.TestXmippRCTWorkflow"]

    # Scipion test blacklist - these wont be executed with the rest of pyworkflow tests
    SCIPION_TESTS_BLACKLIST = (SCIPION_LONG_TESTS +
                               ["pyworkflow.tests.em.workflows.test_parallel_gpu_queue.TestNoQueueSmall",
                                "pyworkflow.tests.em.workflows.test_parallel_gpu_queue.TestNoQueueALL",
                                "pyworkflow.tests.em.workflows.test_parallel_gpu_queue.TestQueueSmall",
                                "pyworkflow.tests.em.workflows.test_parallel_gpu_queue.TestQueueALL",
                                "pyworkflow.tests.em.workflows.test_parallel_gpu_queue.TestQueueSteps",
                                "pyworkflow.tests.em.workflows.test_workflow_existing.TestXmippWorkflow",
                                "relion.tests.test_protocols_relion3.Relion3TestMultiBody",
                                "emxlib.tests.test_workflow_emx.TestEmxWeb",
                                "pwem.tests.workflows.test_parallel_gpu_queue.TestQueueSteps",
                                "pwem.tests.workflows.test_parallel_gpu_queue.TestQueueSmall",
                                "pwem.tests.workflows.test_parallel_gpu_queue.TestQueueALL",
                                "tomo.tests.test_tomo_base.TestTomoAssignAlignment",
                                "spider.tests.test_protocols_spider_align.TestSpiderAlign",
                                "cryosparc2.tests.test_protocols_cryosparc2.TestCryosparcGlobalCtfRefinement",
                                "pwperformance.tests.test_exportsteps.TestExportSteps",
                                'pwperformance.tests.test_profiling_load'])

    ################### Xmipp settings ##################
    # builder prefixes
    XMIPP_INSTALL_PREFIX = 'Install_Xmipp_'
    XMIPP_TESTS = 'xmipp_'
    XMIPP_BUNDLE_TESTS = 'xmipp_bundle_'
    XMIPP_DOCS_PREFIX = 'xmipp_docs_'
    # slack channel
    XMIPP_SLACK_CHANNEL = "xmipp"

    XMIPP_SDEVEL_DOCS_ROOT = "/home/buildbot/devel"
    XMIPP_SDEVEL_C_DOCS_PATH = "/home/buildbot/devel/xmippDoc/html"
    XMIPP_SDEVEL_PY_DOCS_PATH = "/home/buildbot/devel/xmippPythonDoc/html"
    XMIPP_SDEVEL_JAR_DOCS_PATH = "/home/buildbot/devel/xmippJavaDoc/html"

    XMIPP_SDEVEL_C_DOCS_REPO = "git@github.com:I2PC/xmippDoc.git"
    XMIPP_SDEVEL_PY_DOCS_REPO = "git@github.com:I2PC/xmippPythonDoc.git"
    XMIPP_SDEVEL_JAR_DOCS_REPO = "git@github.com:I2PC/xmippJavaDoc.git"


    # xmipp.conf variables
    CUDA = 'True'
    NVCC = 'nvcc'
    NVCC_CXXFLAGS = "--x cu -D_FORCE_INLINES -Xcompiler -fPIC -Wno-deprecated-gpu-targets -ccbin g++-5"
    NVCC_LINKFLAGS = '-L/usr/local/cuda/lib64'
    LD_LIBRARY_PATH = '/usr/local/cuda-10.2/lib64:/home/buildbot/devel/scipion/software/lib:/home/buildbot/anaconda3/envs/develEnv/lib'
    CUDA_BIN = '/usr/local/cuda-10.2/bin'
    PROD_LD_LIBRARY_PATH = '/usr/local/cuda-10.2/lib64:/home/buildbot/prod/scipion/software/lib:/home/buildbot/prod/condaenvs/prodEnv/lib'
    XMIPP_BUNDLE_VARS = ["LD_LIBRARY_PATH", "PATH", "PYTHONPATH",
                         "XMIPP_HOME", "XMIPP_SRC"]
