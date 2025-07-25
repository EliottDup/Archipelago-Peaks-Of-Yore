# Peaks of Yore Setup Guide

## Install using r2modman

### Install r2modman

Head on over to the `r2modman` page on Thunderstore and follow the installation instructions.

[r2modman Page](https://thunderstore.io/package/ebkr/r2modman/)

### Install the PeaksOfArchipelago Mod using r2modman

You can install the PeaksOfArchipelago mod using `r2modman` in one of two ways.

[Mod Download Page](https://thunderstore.io/c/peaks-of-yore/p/c0der23/PeaksOfArchipelago/)

One, you can use the Thunderstore website and click on the "Install with Mod Manager" link.

You can also use the mod manager directly: open `r2modman` > find `Peaks of Yore` > select game > create new profile >
select profile > online > search for "Archipelago" in the `r2modman` interface.
The mod manager should automatically install all necessary dependencies as well.

### THERE IS NO SUPPORT FOR OTHER MODS, USE THEM AT YOUR OWN RISK


## Running the Modded Game

Click on the `Start modded` button in the top left in `r2modman` to start the game with the Archipelago mod installed.

## Configuring your YAML File
### What is a YAML and why do I need one?
You can see the [basic multiworld setup guide](/tutorial/Archipelago/setup/en) here on the Archipelago website to learn 
about why Archipelago uses YAML files and what they're for.

### Where do I get a YAML?
You can use the [game options page](../player-options) here on the Archipelago 
website to generate a YAML using a graphical interface.


## Joining an Archipelago Session
### Connecting to server
Once the game is launched, if everything is installed correctly, you should see a button **Mods** on the main menu.

After clicking on **Mods** to open the in-game mod manager, you should see all the installed mods,
and go to the Peaks Of Archipelago config, this is where you connect to
the server, enter your slot name (the name entered when preparing your yaml file), the hostname and port so for
example: `archipelago.gg:60324` becomes `hostname=archipelago.gg` and `port=60324`, add a password if necessary.

![an image showing the steps necessary to connect to the AP server](https://github.com/EliottDup/image-repo/blob/909de8bd643c3a67c3a431c8608db8477d4fdf99/settings.png?raw=true)

The auto connect option will connect automatically when the game is restarted later but may fail if the port has
changed, which might happen if the server has been offline for a while.

Once everything is entered click the Connect button to connect to the server, and if everything is correct
you should be connected and a green notification saying `Connection Successful` should pop up near the center of your screen.
If the connection fails, showing `Connection failed, see the console for more details` in red, 
the console that opened together with the game should give more information about the fail.

To start the game, begin on a new save, to continue, use the same save you have used before.

**WARNING**: Loading vanilla (unmodded) saves has a **very high** probability of breaking progression.

### Gameplay
When playing randomised peaks of yore, tool unlocking, books, and most other things in your cabin are turned into items,
and therefore not unlocked through normal progression.
Summiting peaks and collecting things on peaks no longer count to normal progression, and instead send items to the
multiworld.

**Warning**: The Alps DLC has not been implemented yet, so going to the Alps may result in unforeseen consequences.
