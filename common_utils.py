import re


# *****************************************************************************
#                                   FUNCTIONS
# *****************************************************************************
def changeConfVar(varName, varValue, file="config/scipion.conf", escapeSlash=False):
    """Wrapper of the command line tool sed to change variable values.
    Please note that some characters like / must be escaped to work.
    Usage example:
    nvcc_linkflags = '-L/usr/local/cuda/lib64'.replace('/', '\/')
    installXmippSteps.addStep(
        ShellCommand(command=changeConfVar('NVCC_LINKFLAGS', nvcc_linkflags, 'xmipp.conf'),
                     name='Set NVCC_LINKFLAGS',
                     description='Set NVCC_LINKFLAGS',
                     descriptionDone='Set NVCC_LINKFLAGS',
                     timeout=300)
    )"""
    if escapeSlash:
        varValue = varValue.replace('/', '\/')
    command = ['bash', '-c', 'sed -i -e '
                             '"s/%s = .*/%s = %s/" '
                             '%s' % (varName, varName, varValue, file)]

    return command

# *****************************************************************************
#               DYNAMIC TEST FACTORY
# *****************************************************************************
from buildbot.plugins import steps, util
from buildbot.process import buildstep, logobserver
from twisted.internet import defer
from settings import timeOutExecute


class GenerateStagesCommand(buildstep.ShellMixin, steps.BuildStep):

    def __init__(self, **kwargs):
        self.rootName = kwargs.pop('rootName', '')
        self.targetTestSet = kwargs.pop('targetTestSet', 'pyworkflow')
        self.blacklist = kwargs.pop('blacklist', [])
        self.stageEnvs = kwargs.pop('stageEnvs', {})
        self.env = kwargs.pop('env', {})
        self.pattern = kwargs.pop('pattern', '')
        self.stagePrefix = kwargs.pop('stagePrefix', [])
        kwargs = self.setupShellMixin(kwargs)
        steps.BuildStep.__init__(self, **kwargs)
        self.observer = logobserver.BufferLogObserver()
        self.addLogObserver('stdio', self.observer)
        self.timeout = kwargs.get('timeout', None) or timeOutExecute

    def extract_stages(self, stdout, rootName=None):
        stages = []
        mainProgram = 'scipion' if rootName != "Xmipp bundle: " else 'xmipp'
        importErrorTxt = 'Error'
        stages = []
        for line in stdout.split('\n'):
            stage = str(line.strip())
            if stage:
                if self.pattern:
                    if re.match(self.pattern, stage):
                        stages.append(stage)
                else:
                    steps = stage.split(' ')
                    if 'Error loading the test' in stage and steps[-1] not in self.blacklist:
                        # from buildbot.process.buildstep import BuildStepFailed
                        # raise BuildStepFailed(stage)
                        # append stage anyway, we'll see a failed step for this stage
                        stages.append(steps[-1])

                    if len(steps) == 3 or importErrorTxt in stage:
                        if steps[-1].split('.', 1)[0] == self.targetTestSet:
                            if steps[0] == mainProgram:
                                if (steps[1]) and (steps[1] == "test"):
                                    if steps[-1] and steps[-1] not in self.blacklist:
                                        stages.append(steps[-1])
        return stages

    @defer.inlineCallbacks
    def run(self):
        # run './build.sh --list-stages' to generate the list of stages
        cmd = yield self.makeRemoteShellCommand()
        yield self.runCommand(cmd)

        # if the command passes extract the list of stages
        result = cmd.results()
        if result == util.SUCCESS:
            # create a ShellCommand for each stage and add them to the build
            testShellCommands = []
            env = self.env
            for stage in self.extract_stages(self.observer.getStdout()):

                env.update(self.stageEnvs.get(stage, {}))
                testShellCommands.append(steps.ShellCommand(
                    command=self.stagePrefix + stage.strip().split(),
                    name=stage,
                    description="Testing %s" % self.rootName + stage.split('.')[-1],
                    descriptionDone=self.rootName + stage.split('.')[-1],
                    timeout=self.timeout,
                    env=env))
            if len(testShellCommands) == 0:
                defer.returnValue(util.FAILURE)
            self.build.addStepsAfterCurrentStep(testShellCommands)

        defer.returnValue(result)
