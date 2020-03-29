from rest_framework import serializers


class WordInfo(object):
    def __init__(self, definition, ipa, category, audio):
        self.definition = definition
        self.ipa = ipa
        self.category = category
        self.audio = audio
