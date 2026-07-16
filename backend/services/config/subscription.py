import json

from pathlib import Path


CONFIG_FILE = (

    Path(__file__)

    .parent.parent.parent

    / "config"

    / "subscription.json"

)


def load_subscription():

    with open(

        CONFIG_FILE,

        "r",

        encoding="utf-8"

    ) as f:

        return json.load(f)
if __name__ == "__main__":

    config = load_subscription()

    print(config)