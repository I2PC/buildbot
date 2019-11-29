# BUILDBOT

Unit tests for Scipion and its plugins.


# BUILDBOT MASTER

Buildbot master is in charge of the configuration. It basically knows what to run 
and when to do it by reading `master.cfg`. However the code is actually run in a 
separate machine, the **buildbot worker**. The main implication of this, is that 
at the time we launch buildbot master, we DO NOT HAVE ACCESS TO ACTUAL RUNTIME INFORMATION, 
like paths, environment variables, etc. But there are ways to work around this. 

## Restarting the master

1. We ssh into the machine: 

```bash
$ ssh -X buildbot@arquimedes
```

### Testing changes

2. Are we just getting started with some new changes we added to buildbot? Then 
we probably **don't want to notify slack** users of any failures. 
Set **`DONT_NOTIFY_SLACK`** before restarting buildbot:

```bash
buildbot@arquimedes:~$ export DONT_NOTIFY_SLACK=True
```

We probably need to bring any changes we made. This repository is in `~/master`:
```bash
buildbot@arquimedes:~$ cd master
buildbot@arquimedes:~$ git pull
```

3. Stop buildbot service. 
```
buildbot@arquimedes:~$ sudo systemctl stop buildbot-master
```

4. Restart without `systemctl` to test changes
```
buildbot@arquimedes:~$ buildbot restart ~/master
```

5. Once you're confident with your changes, stop buildbot and start with `systemctl`. 
```
buildbot@arquimedes:~$ buildbot stop ~/master
buildbot@arquimedes:~$ sudo systemctl start buildbot-master
```

### Restarting buildbot service
If you don't want to test any changes and just want to restart buildbot, just do:
```
buildbot@arquimedes:~$ sudo systemctl restart buildbot-master
```
You can also check the status:
```
buildbot@arquimedes:~$ sudo systemctl status buildbot-master
● buildbot-master.service - BuildBot master service
   Loaded: loaded (/etc/systemd/system/buildbot-master.service; enabled; vendor preset: enabled)
   Active: active (running) since Wed 2019-04-10 16:38:46 CEST; 18h ago
 Main PID: 15398 (buildbot)
    Tasks: 4 (limit: 4915)
   CGroup: /system.slice/buildbot-master.service
           └─15398 /usr/bin/python /usr/local/bin/buildbot start --nodaemon

Apr 10 16:38:46 arquimedes.cnb.csic.es systemd[1]: Started BuildBot master service.
```

## settings.py

In this file we can find all the constants that we need for the builders. Please 
note that the worker name and the worker pass are taken from the environment 
(i.e. they need to be set for example in `.bash_profile`).

One key part of `settings.py` is `branchsDict`. At the time of this writing, 
we have two orchestrator builders: `devel` and `prod`. In the variable `branchsDict` 
we can assign which branches we want to build in each orchestrator. As we can see, 
we can change the many of the branches we want to test in DEVEL: docs, xmipp, 
and scipion. In prod we only choose the scipion branch because we don't build 
docs, and because we install xmipp from pypi.

```python
branchsDict = {DEVEL_GROUP_ID: {SCIPION_BUILD_ID: 'release-2.0.0-fixes',
                                XMIPP_BUILD_ID: 'release-19.03-fixes',
                                DOCS_BUILD_ID: 'release-2.0.0'},
               PROD_GROUP_ID: {
                   SCIPION_BUILD_ID: 'release-2.0.0-fixes'
               }}
```

## Using properties
Since the master doesn't have access to the run environment, we have to use buildbot properties to use certain values. For example, in the master we don't know the exact path of our `SCIPION_HOME`. What we can achieve with properties is basically telling buildbot "hey, we'll use `SCIPION_HOME` here, but just wait until we're running on the worker to get the actual value". 

### Common properties: SCIPION_HOME
Let's take the example of `SCIPION_HOME`. This variable will be useful for us in different builders, like the one in charge of installing Xmipp in devel mode, but we don't know beforehand the whole path of `SCIPION_HOME`, so we need to set it at run time. Like you already know, there are two orchestrators: devel and prod. Let's use devel as an example. All of its steps are defined in the [`develBuildGroupFactory`](https://github.com/yaizar/buildbot/blob/master/master.cfg#L102). One of these steps is [`setCommonProperties`](https://github.com/yaizar/buildbot/blob/master/master.cfg#L106):

```python
def setCommonProperties(groupId, factorySteps=None):
    factorySteps = factorySteps or util.BuildFactory()
    factorySteps.addStep(steps.SetPropertyFromCommand(command="echo $PWD",
                                                      property="SCIPION_HOME",
                                                      name="Set SCIPION_HOME",
                                                      description="Set SCIPION_HOME",
                                                      descriptionDone="SCIPION_HOME set"))

    factorySteps.addStep(steps.SetProperty(property='SCIPION_LOCAL_CONFIG',
                                           value="~/.config/scipion/scipion_%s.conf" % groupId,
                                           name="Set SCIPION_LOCAL_CONFIG",
                                           description="Set SCIPION_LOCAL_CONFIG",
                                           descriptionDone="SCIPION_LOCAL_CONFIG set"))

    factorySteps.addStep(steps.SetPropertyFromCommand(command='echo $(dirname "$(pwd)")',
                                                      property="BUILD_GROUP_HOME",
                                                      name="Set BUILD_GROUP_HOME",
                                                      description="Set BUILD_GROUP_HOME",
                                                      descriptionDone="BUILD_GROUP_HOME set"
                                                      ))
    return factorySteps
```

The orchestrators are set up so that their working directory will be the `SCIPION_HOME`. Therefore, we can know the path by executing the command `echo $PWD`. Once this is executed, the develBuilder has access to this property, and it can be accessed by using `util.Property("SCIPION_HOME")`:

In `develBuildGroupFactory`, it is used in the dict `props` so that we can pass it to other builders. See how we pass it to the XMIPP install builder:
```python
props = {
        'SCIPION_HOME': util.Property("SCIPION_HOME"),
        "SCIPION_LOCAL_CONFIG": util.Property("SCIPION_LOCAL_CONFIG")}
        
factorySteps.addStep(
    steps.Trigger(schedulerNames=[XMIPP_INSTALL_PREFIX + groupId],
                  haltOnFailure=True,
                  waitForFinish=True,
                  set_properties=props))
```

So now the Xmipp install builder has access to this property. 

#### Properties as env variables:
However, having access to this property is limited to buildbot. For the Xmipp installation to know where `SCIPION_HOME` is, we need to set it as an environment variable. Check how we pass it as `env=installEnv` when we create the `INSTALL_XMIPP_DEVEL` in `master_xmipp.py`: 

```
    installEnv = {'SCIPION_HOME': util.Property('SCIPION_HOME')}
    installEnv.update(cudaEnv)
    bundleEnv = {}
    bundleEnv.update(cudaEnv)
    bundleEnv.update(installEnv)
    [ . . . . . . ]
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
```

#### Properties in strings
If we have to concatenate the value of a property with another string, we need to use the function Interpolate. Check how it's done in installXmippFactory:

```
  installXmippSteps.addStep(
      steps.SetPropertyFromCommand(command='echo $PWD', property='XMIPP_HOME'))

  linkToSitePkgs = ['ln', '-fs', util.Interpolate('%(prop:XMIPP_HOME)s/src/scipion-em-xmipp/xmipp3'),
                    util.Interpolate('%(prop:SCIPION_HOME)s/software/lib/python2.7/site-packages/')]
```

## Adding a plugin

The file `getplugins.json` contains the list of plugins that are tested. The order of the plugins is important because it takes dependencies into account. To test a new plugin you only need to add it to this list :)


# BUILDBOT WORKER

## Opening a failed test
We ssh into the machine: 

```bash
$ ssh -X buildbot@einstein.cnb.csic.es
```

We will show up by default at Scipion devel directory. Before we launch Scipion, we need to select the right config file:

```bash
buildbot@einstein:~/scipionBot/devel/scipion$ export   SCIPION_LOCAL_CONFIG=~/.config/scipion/scipion_devel.conf
```

Now we can check any test that failed, for example TestEmanRefine2D:
```bash
buildbot@einstein:~/scipionBot/devel/scipion$ ./scipion project TestEmanRefine2D
```

If we wanted to do this but with prod, we would have to navigate to `~/scipionBot/prod/scipion`, use the config `scipion_prod.conf`.

## Restarting the worker
If for whatever reason you need to restart the worker, navigate to `~/scipionBot` and run:

```bash
buildbot@einstein:~/scipionBot/devel/scipion$ sudo systemctl restart buildbot-worker
```
We can also check the status, start and stop the worker by replacing `restart` with `status`, `start` or `stop`
