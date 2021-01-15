# Jabberbot

## Installation Instructions

#### vector-python-sdk:
Jabberbot was built using ikkez's fork of the Vector SDK (v0.7.2) in order to take advantage of some additional features.
Please follow the correct installation instructions for your operating system:
> https://vector.ikkez.de/initial.html

#### PyYaml:
Jabberbot also requires PyYaml, which can be installed using the following:
```
    pip install --user pyyaml
```

## Introduction to Jabberbot
Jabberbot is my first project that aims to turn my adorable little Vector robot into an ammusing character that chats to himself and reacts to things arround him with speech. The simplest way to achieve this was to use the SDK.

After some googling and a little reseach, I came across ["vectorator" created by TurkMcGill](https://github.com/TurkMcGill/vectorator). I played around with this little python app for a while before I moved on to righting my own. So Jabberbot is highly inspired by vectorators key features, which I have imitated and improved upon.

I have added additional features such as a "Do-Not-Disturb" timeframe and random chit-chat. 

I borrowed the random dialogue, jokes and "fact of the day" files that were written by TurkMcGill for vecorator and have either customised or added to them. I have also added additional entries to these to increase the randomness of what Vector will say. There have also been addtional lists added for further randomisation.

All of Jabberbot's dialogue files, located in the 'lists' folder, *are* python files but, they contain either JSON data or simple string arrays:

## Jabberbot's "inital" dialogue
This file is Jabberbots first port-of-call when reacting to an event.

```
DIALOGUE = {
    "_name_": {
        "minimum_delay": ##,
        "maximum_delay": ##,
        "lines": [...]
    }
}
```

- `_name_`        - these are the event/trigger names. **Don't change these!**
- `minimum_delay` - is the minimum number of seconds.
- `maximum_delay` - is the maximum number of seconds.
- `lines`         - this is a string array of dialogue lines for Vector to say.

**NOTE:** Jabberbot will wait a random number of seconds before reacting to an event/trigger, that is calculated between the minimum_delay and maximum_delay values. This is also affected by the `chattiness` option _(see below)_.

### Words in Curly Braces:
Certain default lines of dialogue include various tag words enclosed in curly braces. When Jabberbot detects a perticular tag it will be randomly replaced them with synonyms in order to add some more randomness. These synonyms are located in the 'list/synonyms/' folder.
There are currently six synonym tags which you can customise:
- `{good}`
- `{interesting}`
- `{object}`
- `{scary}`
- `{swear_words}`
- `{weird}`

An additional tag of `{name}` can be used to inject the named human Vector has recently seen. If he has NOT seen anyone he recognizes in the last few seconds then `{name}` will be removed. So Vector will either say, "Hey John, here is an interesting fact." Or he will say, "Hey , here is an interesting fact."

## Chit-Chat, Dreams, Jokes and Facts
In an effort to make Vector more understandable, extra commas and mispelled words are included in the various dialogue files. These are intentional and are not spelling/grammatical errors.

## Configuration
There are several options that can be customised to adjust Vector to react the way you would like him to.

- `chattiness   = [1 to 10]`
- `sound_volume = [1 to 5]`
- `voice_volume = [1 to 5]`
- `dnd_start    = [0 to 23]`
- `dnd_end      = [0 to 23]`

The chattiness setting (1 to 10) affects the minimum_delay and maximum_delay values, mentioned above, used to geneerate the random number of seconds used before reacting to an event/trigger.

Be aware that any changes to chattiness might not be noticed striaght away, because timestamps are recorded after Vector speaks. Updating chattiness may not have any impact until the next time Vector tells a joke for example. In order to can get around this, you can delete the timestamps.csv file to reset Jabberbot.
