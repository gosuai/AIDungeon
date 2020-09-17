import logging
import os
import random
from contextlib import asynccontextmanager

import aiohttp
import yaml

from .story import grammars
from .story.story_manager import Story
from .story.utils import (
    console_print, player_won, first_to_second_person, player_died, get_similarity, cut_trailing_sentence,
)

from . import settings

logger = logging.getLogger(__name__)


def random_story(story_data):
    # random setting
    settings = story_data["settings"].keys()
    n_settings = len(settings)
    n_settings = 2
    rand_n = random.randint(0, n_settings - 1)
    for i, setting in enumerate(settings):
        if i == rand_n:
            setting_key = setting

    # random character
    characters = story_data["settings"][setting_key]["characters"]
    n_characters = len(characters)
    rand_n = random.randint(0, n_characters - 1)
    for i, character in enumerate(characters):
        if i == rand_n:
            character_key = character

    # random name
    name = grammars.direct(setting_key, "character_name")

    return setting_key, character_key, name, None, None


def select_game():
    with open(f'{os.path.dirname(__file__)}/story/story_data.yaml') as stream:
        data = yaml.safe_load(stream)

    return random_story(data)


def get_custom_prompt():
    context = ""
    console_print(
        "\nEnter a prompt that describes who you are and the first couple sentences of where you start "
        "out ex:\n 'You are a knight in the kingdom of Larion. You are hunting the evil dragon who has been "
        + "terrorizing the kingdom. You enter the forest searching for the dragon and see' "
    )
    prompt = input("Starting Prompt: ")
    return context, prompt


def get_curated_exposition(
    setting_key, character_key, name, character, setting_description
):
    name_token = "<NAME>"
    try:
        context = grammars.generate(setting_key, character_key, "context") + "\n\n"
        context = context.replace(name_token, name)
        prompt = grammars.generate(setting_key, character_key, "prompt")
        prompt = prompt.replace(name_token, name)
    except Exception:
        context = (
            "You are "
            + name
            + ", a "
            + character_key
            + " "
            + setting_description
            + "You have a "
            + character["item1"]
            + " and a "
            + character["item2"]
            + ". "
        )
        prompt_num = random.randint(0, len(character["prompts"]))
        prompt = character["prompts"][prompt_num]

    return context, prompt


@asynccontextmanager
async def connect_to_aidungeon(url: str = f'http://{settings.WEB_HOST}:{settings.WEB_PORT}'):
    async with aiohttp.ClientSession(raise_for_status=True) as session:
        (
            setting_key,
            character_key,
            name,
            character,
            setting_description,
        ) = select_game()

        logger.debug(f"Generating new story: {setting_key} {character_key} {name} {character} {setting_description}")
        context, prompt = get_curated_exposition(setting_key, character_key, name, character, setting_description)
        generator = RemoteGPTGenerator(session, url)
        block = await generator.generate(context + prompt)
        block = cut_trailing_sentence(block)
        story = Story(
            context + prompt + block,
            context=context,
            game_state=None,
        )
        yield AiDungeonClient(generator, story)


class RemoteGPTGenerator:
    def __init__(self, session, url):
        self.session = session
        self.url = f'{url}{settings.AIDUNGEON_PATH}'

    async def generate(self, prompt: str):
        response = await self.session.post(self.url, json=dict(prompt=prompt))
        return (await response.json())['text']


class AiDungeonClient:
    def __init__(self, generator, story):
        self.generator = generator
        self.story = story

    async def ask(self, action: str):
        if len(action) > 0 and action[0] == "/":
            split = action[1:].split(" ")  # removes preceding slash
            command = split[0].lower()
            if command == "restart":
                self.story.actions = []
                self.story.results = []
                return f"Game restarted.\n{self.story.story_start}"

            elif command == "revert":
                if len(self.story.actions) == 0:
                    return "You can't go back any farther."

                self.story.actions = self.story.actions[:-1]
                self.story.results = self.story.results[:-1]
                console_print("Last action reverted.")
                if len(self.story.results) > 0:
                    console_print(self.story.results[-1])
                else:
                    console_print(self.story.story_start)

            else:
                return f"Unknown command: {command}"
        else:
            return await self.process_action(action)

    async def process_action(self, action: str):
        if action == "":
            return await self.act(action)
        elif action[0] == '"':
            action = "You say " + action
        else:
            action = action.strip()

            if "you" not in action[:6].lower() and "I" not in action[:6]:
                action = action[0].lower() + action[1:]
                action = "You " + action

            if action[-1] not in [".", "?", "!"]:
                action = action + "."

            action = first_to_second_person(action)
            action = "\n> " + action + "\n"

        result = "\n" + await self.act(action)
        if len(self.story.results) >= 2:
            similarity = get_similarity(
                self.story.results[-1], self.story.results[-2]
            )
            if similarity > 0.9:
                self.story.actions = self.story.actions[:-1]
                self.story.results = self.story.results[:-1]
                return "Woops that action caused the model to start looping. Try a different action to prevent that."

        if player_won(result):
            return result + "\nCONGRATS YOU WON"
        elif player_died(result):
            return result + "\nYOU DIED. GAME OVER"
        else:
            return result

    async def act(self, action_choice: str):
        result = await self.generate_result(action_choice)
        self.story.add_to_story(action_choice, result)
        return result

    async def generate_result(self, action: str):
        return await self.generator.generate(self.story_context() + action)

    def story_context(self):
        return self.story.latest_result()
