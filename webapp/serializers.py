from rest_framework import serializers


class WordSerializer(serializers.Serializer):
    definition = serializers.CharField(max_length=200)
    # lemma = serializers.CharField(max_length=200)
    ipa = serializers.CharField(max_length=200)
    category = serializers.CharField(max_length=200)
    audio = serializers.URLField(max_length=200)