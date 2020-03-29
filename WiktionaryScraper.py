from urllib.request import urlopen
import urllib.parse
from bs4 import BeautifulSoup
import csv
import os.path


def get_language_code(language):
    with open('language_codes.csv', 'r', encoding='utf-8') as csvR:
        reader = csv.reader(csvR)
        for row in reader:
            if row[0] == language:
                return row[2]


def get_language_name(iso_code):
    with open('language_codes.csv', 'r', encoding='utf-8') as csvR:
        reader = csv.reader(csvR)
        for row in reader:
            if row[2] == iso_code:
                return row[1]


def define(word, language, pos=None):
    lang = get_language_code(language)
    language = get_language_name(lang)
    pos_list = ['Noun', 'Verb', 'Adjective', 'Adverb', 'Preposition', 'Conjunction', 'Pronoun', 'Determiner', 'Numeral',
                'Proper noun', 'Article']
    definitions = []
    pos_correct = False

    if pos in pos_list:
        pos_list.remove(pos)

    if word == '||':
        return ''

    word = word.strip()
    word = word.replace(' ', '_')
    # encodes the word in a way that the webpage will recognise unicode
    # must convert to lowercase to prevent hang from redirecting but leads to ignoring proper nouns and German nouns
    quote_page = 'https://en.wiktionary.org/wiki/' + urllib.parse.quote(word.lower())

    try:
        page = urlopen(quote_page)
    except:
        print('No web page was found at ' + quote_page)
        return ''

    soup = BeautifulSoup(page, 'html.parser')

    # removes example sentences within definition entries - may want to extract these separately
    while soup.dl is not None:
        soup.dl.decompose()

    while soup.ul is not None:
        soup.ul.decompose()

    # find the language section of the page
    lang_header = soup.find(id=language)
    if lang_header is None:
        print(language + ' header not found')
        return ''

    # loops through HTML following the language header
    next_section = lang_header.find_all_next()

    if next_section is None:
        print('next_section not found')
    else:
        for item in next_section:
            # find beginning of part of speech section
            try:
                if pos != '':
                    if pos in item.span['id']:
                        pos_correct = True
                else:
                    for p in pos_list:
                        if p in item.span['id']:
                            part_of_speech = p
                            pos_correct = True

            except KeyError:
                # item has no id attribute, do nothing
                x = 1
            except TypeError:
                # item has no span, do nothing
                x = 1

            if pos_correct:
                # stop listing definitions if encounter a different POS
                if pos != '':
                    try:
                        for part in pos_list:
                            if part in item.span['id']:
                                different_pos = True
                                break
                        if different_pos:
                            break
                    except:
                        x = 1

                if item.parent.name == 'td':
                    continue

                try:
                    if lang not in item['lang']:
                        break
                except:
                    x = 1

                try:
                    if 'References' in item['id']:
                        break
                except:
                    x = 1

                if item.name == 'ol':
                    for e in item.descendants:
                        if e.name == 'li':
                            definition = e.get_text().rstrip()

                            # finds pos if unspecified
                            if pos == '':
                                definition = part_of_speech + ': ' + definition

                            definitions.append(definition)

        return definitions


"""
Takes an English word and returns the translation in a given target language.
"""
def translate(word, target_language, pos=None):
    lang = get_language_code(target_language)
    translation = None
    pos_list = ['Noun', 'Verb', 'Adjective', 'Adverb', 'Preposition', 'Conjunction', 'Pronoun', 'Determiner', 'Numeral',
                'Proper_noun', 'Personal_pronoun', 'Article', 'Interjection']
    if pos in pos_list:
        pos_list.remove(pos)

    word = word.replace(' ', '_')

    quote_page = 'https://en.wiktionary.org/wiki/' + urllib.parse.quote(word)

    try:
        page = urlopen(quote_page)
    except:
        print('No web page was found at ' + quote_page + '. Did you enter a valid English word?')
        return

    soup = BeautifulSoup(page, 'html.parser')

    body = soup.find(class_='mw-parser-output')
    if body is None:
        print('Body not found')
        return ''

    english_header = body.find(id='English')
    if english_header is None:
        print('English header not found')
        return ''
    pos_correct = False

    # loops through HTML following the English header
    next_section = english_header.parent.find_all_next()
    lang_limit = None
    trans_row = []

    if next_section is None:
        print('next_section not found')
        return ''
    else:
        for item in next_section:

            # find beginning of part of speech section
            if not pos_correct:
                try:
                    if pos in item.span['id']:
                        pos_correct = True
                except KeyError:
                    # item has no id attribute, do nothing
                    continue
                except TypeError:
                    # item has no span, do nothing
                    pos_correct = pos_correct
                    # continue?

            if pos_correct:

                # finds limit of part of speech section
                for part in pos_list:
                    try:
                        if part in item.span['id']:
                            lang_limit = item
                            break
                    except TypeError:
                        # item has no span, do nothing
                        break
                    except KeyError:
                        # item has no id attribute, do nothing
                        break

                # halts execution if limit reached
                if lang_limit is not None:
                    if item == lang_limit:
                        break  # breaks whole loop

                try:  # find the translation navframe
                    if 'NavFrame' in item['class']:
                        # get the header containing the definition of the translation
                        definition = item.div.get_text()

                        # if the target language contains a translation for that definition, extract it
                        for element in item.descendants:
                            try:
                                if element.get('lang') is not None:
                                    if element.get('lang') == lang:
                                        # prevents returning Serbian Cyrillic
                                        if lang == 'sh' and 'Cyrl' in element['class']:
                                            continue
                                        translation = element.get_text()
                                        break
                                        # extract all translations with their headers
                                        trans_row.append(definition + ' - ' + translation)
                            except AttributeError:
                                # element has no lang attribute, do nothing
                                continue
                        if translation is not None:
                            break
                except KeyError:
                    # item has no class attribute, do nothing
                    continue

        if translation is None:
            quote_page = 'https://en.wiktionary.org/wiki/' + urllib.parse.quote(word) + '/translations#' + pos

            try:
                page = urlopen(quote_page)
            except:
                print('No web page was found at ' + quote_page + '. Did you enter a valid English word?')
                return ''

            soup = BeautifulSoup(page, 'html.parser')

            body = soup.find(class_='mw-parser-output')
            if body is None:
                print('Body not found')
                return ''

            english_header = body.find(id='English')
            if english_header is None:
                print('English header not found')
                return ''
            pos_correct = False

            # loops through HTML following the English header
            next_section = english_header.parent.find_all_next()
            lang_limit = None
            found = False
            trans_row = []

            if next_section is None:
                print('next_section not found')
                return ''
            else:
                for item in next_section:

                    # find beginning of part of speech section
                    if not pos_correct:
                        try:
                            if pos in item.span['id']:
                                pos_correct = True
                        except KeyError:
                            # item has no id attribute, do nothing
                            continue
                        except TypeError:
                            # item has no span, do nothing
                            pos_correct = pos_correct

                    if pos_correct:

                        # finds limit of part of speech section
                        for part in pos_list:
                            try:
                                if part in item.span['id']:
                                    lang_limit = item
                                    break
                            except TypeError:
                                # item has no span, do nothing
                                break
                            except KeyError:
                                # item has no id attribute, do nothing
                                break

                        # halts execution if limit reached
                        if lang_limit is not None:
                            if item == lang_limit:
                                break  # breaks whole loop

                        try:  # find the translation navframe
                            if 'NavFrame' in item['class']:
                                # get the header containing the definition of the translation
                                definition = item.div.get_text()

                                # if the target language contains a translation for that definition, extract it
                                for element in item.descendants:
                                    try:
                                        if element.get('lang') is not None:
                                            if element.get('lang') == lang:
                                                translation = element.get_text()
                                                # extract all translations with their headers
                                                trans_row.append(definition + ' - ' + translation)
                                                found = True
                                    except AttributeError:
                                        # element has no lang attribute, do nothing
                                        continue
                        except KeyError:
                            # item has no class attribute, do nothing
                            continue

    if translation is None:
        translation = ''

    return translation


def scrape_ipa(word, language, pos=None):
    lang = get_language_code(language)
    language = get_language_name(lang)
    words = []
    ipa_row = []
    ipa_list = []
    pos_list = ['Noun', 'Verb', 'Adjective', 'Adverb', 'Preposition', 'Conjunction', 'Pronoun', 'Determiner', 'Numeral',
                'Proper noun', 'Article']
    pos_correct = False
    ipa = None

    ipa_row = []
    if pos in pos_list:
        pos_list.remove(pos)
        # print(pos_list)

    if word == '||':
        return

    word = word.strip()
    word = word.replace(' ', '_')
    # encodes the word in a way that the webpage will recognise unicode
    # must convert to lowercase to prevent hang from redirecting but leads to ignoring proper nouns and German nouns
    # Make sure you compare to glosbe and translate to identify proper nouns.
    quote_page = 'https://en.wiktionary.org/wiki/' + urllib.parse.quote(word.lower())

    try:
        page = urlopen(quote_page)
    except:
        print('No web page was found at ' + quote_page)
        return [word, '']

    soup = BeautifulSoup(page, 'html.parser')

    # find the language section of the page
    lang_header = soup.find(id=language)
    if lang_header is None:
        print(language + ' header not found')
        return [word, '']

    # loops through HTML following the language header
    next_section = lang_header.find_all_next()

    if next_section is None:
        print('next_section not found')
        return [word, '']
    else:
        for item in next_section:
            # find beginning of part of speech section
            try:
                if pos != '':
                    if pos in item.span['id']:
                        pos_correct = True
                else:
                    for p in pos_list:
                        if p in item.span['id']:
                            # print('Found a part of speech header: ' + p)
                            part_of_speech = p
                            # print(part_of_speech)
                            pos_correct = True

            except KeyError:
                # item has no id attribute, do nothing
                x = 1
            except TypeError:
                # item has no span, do nothing
                x = 1

            if pos_correct:
                # print(True)

                # stop listing definitions if encounter a different POS
                if pos != '':
                    try:
                        for part in pos_list:
                            if part in item.span['id']:
                                # print(part)
                                different_pos = True
                                break
                        if different_pos:
                            break
                    except:
                        x = 1

                if item.parent.name == 'td':
                    # print('Ignoring table')
                    continue

                try:
                    if lang not in item['lang']:
                        # print('Different language encountered')
                        break
                except:
                    x = 1

                try:
                    if 'References' in item['id']:
                        # print('References encountered')
                        break
                except:
                    x = 1

                # print ('survived')

                if ipa is None:
                    # ipa_text = lang_header.find_next(class_'IPA')
                    # finds any IPA above - hopefully from new soup
                    for i in item.find_all_previous():
                        try:
                            # print(i['id'])
                            if i['id'] == language:
                                # print('Header reached')
                                # ipa == ''
                                break
                            elif 'Pronunciation' in i['id']:
                                # print('Pronunciation located')
                                ipa_text = i.find_next(class_='IPA')
                                ipa = ipa_text.get_text()
                                # print(ipa)
                                break

                        except:
                            # no id, do nothing
                            continue

        # ipa_row.append(word)
        # if ipa is not None:
        #     ipa_row.append(ipa)
        # else:
        #     ipa_row.append('')
        # print(word, ipa_row)
        if ipa is None:
            ipa = ''

    return ipa


def scrape_category(word, language, pos=None):
    lang = get_language_code(language)
    language = get_language_name(lang)
    pos_list = ['Noun', 'Verb', 'Adjective', 'Adverb', 'Preposition', 'Conjunction', 'Pronoun', 'Determiner', 'Numeral',
                'Proper noun', 'Article']
    pos_correct = False
    cat = None

    if pos in pos_list:
        pos_list.remove(pos)
        # print(pos_list)

    if word == '||':
        return

    word = word.strip()
    word = word.replace(' ', '_')
    # encodes the word in a way that the webpage will recognise unicode
    # must convert to lowercase to prevent hang from redirecting but leads to ignoring proper nouns and German nouns
    # Make sure you compare to glosbe and translate to identify proper nouns.
    quote_page = 'https://en.wiktionary.org/wiki/' + urllib.parse.quote(word.lower())

    try:
        page = urlopen(quote_page)
    except:
        print('No web page was found at ' + quote_page)
        return [word, '']

    soup = BeautifulSoup(page, 'html.parser')

    # find the language section of the page
    lang_header = soup.find(id=language)
    if lang_header is None:
        print(language + ' header not found')
        return [word, '']

    # loops through HTML following the language header
    next_section = lang_header.find_all_next()

    if next_section is None:
        print('next_section not found')
        return [word, '']
    else:
        for item in next_section:
            # find beginning of part of speech section
            try:
                if pos != '':
                    if pos in item.span['id']:
                        pos_correct = True
                else:
                    for p in pos_list:
                        if p in item.span['id']:
                            # print('Found a part of speech header: ' + p)
                            part_of_speech = p
                            # print(part_of_speech)
                            pos_correct = True

            except KeyError:
                # item has no id attribute, do nothing
                x = 1
            except TypeError:
                # item has no span, do nothing
                x = 1

            if pos_correct:
                # print(True)

                # stop listing definitions if encounter a different POS
                if pos != '':
                    try:
                        for part in pos_list:
                            if part in item.span['id']:
                                # print(part)
                                different_pos = True
                                break
                        if different_pos:
                            break
                    except:
                        x = 1

                if item.parent.name == 'td':
                    # print('Ignoring table')
                    continue

                try:
                    if lang not in item['lang']:
                        # print('Different language encountered')
                        break
                except:
                    x = 1

                try:
                    if 'References' in item['id']:
                        # print('References encountered')
                        break
                except:
                    x = 1

                if cat is None:
                    cat_text = item.find_next(class_='gender')
                    if cat_text is not None:
                        cat = cat_text.get_text()
                        print(cat)

    return cat


def scrape_audio(language, word):
    lang = get_language_code(language)

    word = word.replace(" ", "_")
    try:
        url = "https://commons.wikimedia.org/wiki/File:" + lang + "-" + urllib.parse.quote(word) + ".ogg"
        page = urlopen(url)
    except urllib.error.HTTPError:
        print(word + " has no audio.")
        return

    soup = BeautifulSoup(page, 'html.parser')
    link = soup.find(class_="internal")
    ogg_url = link['href']

    try:
        ogg = urlopen(ogg_url)
    except urllib.error.HTTPError:
        print(word + " has no audio.")
        return

    return ogg


def scrape_info(word, language, pos=None, num_definitions=1):
    lang = get_language_code(language)
    language = get_language_name(lang)
    words = []
    ipa_row = []
    ipa_list = []
    definition = ''
    definitions = []
    part_of_speech = ''
    pos_list = ['Noun', 'Verb', 'Adjective', 'Adverb', 'Preposition', 'Conjunction', 'Pronoun', 'Determiner', 'Numeral',
                'Proper noun', 'Article']
    pos_correct = False
    ipa = None
    cat = None

    ipa_row = []
    if pos in pos_list:
        pos_list.remove(pos)
        # print(pos_list)

    if word == '||':
        return

    word = word.strip()
    word = word.replace(' ', '_')
    # encodes the word in a way that the webpage will recognise unicode
    # must convert to lowercase to prevent hang from redirecting but leads to ignoring proper nouns and German nouns
    # Make sure you compare to glosbe and translate to identify proper nouns.
    quote_page = 'https://en.wiktionary.org/wiki/' + urllib.parse.quote(word.lower())

    try:
        page = urlopen(quote_page)
    except:
        try:
            page = urlopen('https://en.wiktionary.org/wiki/' + urllib.parse.quote(word))
        except:
            print('No web page was found at ' + quote_page)
            return [word, '']

    soup = BeautifulSoup(page, 'html.parser')

    # removes example sentences within definition entries - may want to extract these separately
    # must be while as each is decomposed individually
    while soup.dl is not None:
        soup.dl.decompose()

    # find the language section of the page
    lang_header = soup.find(id=language)
    if lang_header is None:
        print(language + ' header not found for ' + word)
        return [word, '']

    # loops through HTML following the language header
    next_section = lang_header.find_all_next()

    if next_section is None:
        print('next_section not found')
        return [word, '']
    else:
        for item in next_section:

            # find beginning of part of speech section
            try:
                if pos != '':
                    if pos in item.span['id']:
                        pos_correct = True
                else:
                    for p in pos_list:
                        if p in item.span['id']:
                            # print('Found a part of speech header: ' + p)
                            part_of_speech = p
                            # print(part_of_speech)
                            pos_correct = True

            except KeyError:
                # item has no id attribute, do nothing
                x = 1
            except TypeError:
                # item has no span, do nothing
                x = 1

            if pos_correct:
                # print(True)

                # stop listing definitions if encounter a different POS
                if pos != '':
                    try:
                        for part in pos_list:
                            if part in item.span['id']:
                                # print(part)
                                different_pos = True
                                break
                        if different_pos:
                            break
                    except:
                        x = 1
                try:
                    if item.parent.name == 'td':
                        # print('Ignoring table')
                        continue
                except AttributeError:
                    x = 1

                try:
                    if lang not in item['lang']:
                        # print('Different language encountered')
                        break
                except:
                    x = 1

                try:
                    if 'References' in item['id']:
                        # print('References encountered')
                        break
                except:
                    x = 1

                # print ('survived')

                if ipa is None:
                    # ipa_text = lang_header.find_next(class_'IPA')
                    # finds any IPA above - hopefully from new soup
                    for i in item.find_all_previous():
                        try:
                            # print(i['id'])
                            if i['id'] == language:
                                # print('Header reached')
                                # ipa == ''
                                break
                            elif 'Pronunciation' in i['id']:
                                # print('Pronunciation located')
                                ipa_text = i.find_next(class_='IPA')
                                ipa = ipa_text.get_text()
                                # print(ipa)
                                break

                        except:
                            # no id, do nothing
                            continue

                if cat is None:
                    cat_text = item.find_next(class_='gender')
                    if cat_text is not None:
                        cat = cat_text.get_text()
                        # print(gender)

                # removes citations from definition
                while soup.ul is not None:
                    soup.ul.decompose()

                # print(item.get_text())
                if item.name == 'ol':
                    # print('!')
                    for e in item.descendants:
                        if e.name == 'li':
                            definition = e.get_text().rstrip()

                            # finds pos if unspecified
                            # print (part_of_speech)
                            if pos == '':
                                # print(definition)
                                definition = part_of_speech + ': ' + definition
                            if num_definitions == 1:
                                break

                            definitions.append(definition)
                        # break;

        # ipa_row.append(word)
        # print(definitions)
        if ipa is None:
            ipa = ''
        if cat is None:
            cat = ''
        if definition is None:
            definition = ''
        if num_definitions > 1:
            definition = definitions

        ipa_row.append(definition)
        ipa_row.append(ipa)
        ipa_row.append(cat)

    return ipa_row
