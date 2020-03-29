from django.shortcuts import render
from rest_framework.renderers import JSONRenderer
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from . serializers import WordSerializer
from rest_framework import serializers
from WiktionaryScraper import scrape_info


class WordInfo:
    def __init__(self, definition, ipa, category,audio):
        self.definition = definition
        self.ipa = ipa
        self.category = category
        self.audio = audio


class APIView(APIView):
    def get(self, request):
        print(request.GET.get('word'), request.GET.get('language'), request.GET.get('pos'))
        info = scrape_info(request.GET.get('word'), request.GET.get('language'), request.GET.get('pos'))
        print(info)
        word_info = WordInfo(info[0], info[1], info[2], info[3])
        print(word_info.definition, word_info.ipa, word_info.category, word_info.audio)
        serializer = WordSerializer(word_info)
        json = JSONRenderer().render(serializer.data)
        print(json)
        return Response(json)


'''class WordList(APIView):

    def get(self):
        #words1 = word.objects.all()
        wordInfo = wiktionaryScraper.scrape_info()
        serializer = WordSerializer(wordInfo, many=False)
        return Response(serializer.data)

    def get(self, request):
        # word_info = scrape_info(self.word, self.language)
        word_info = [request.GET.get('word'), request.GET.get('language')]
        return Response(serializers.Serialize(word_info))'''
