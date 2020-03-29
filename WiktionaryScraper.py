from urllib.request import urlopen
import urllib.parse
from bs4 import BeautifulSoup
import csv


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


def scrape_audio(word, language):
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
    return ogg_url


def scrape_info(word, language, pos, num_definitions=1):
    lang = get_language_code(language)
    language = get_language_name(lang)
    definition = ''
    definitions = []
    pos_list = ['Noun', 'Verb', 'Adjective', 'Adverb', 'Preposition', 'Conjunction', 'Pronoun', 'Determiner', 'Numeral',
                'Proper noun', 'Article']
    pos_correct = False
    ipa = None
    cat = None

    word_info = []
    if pos in pos_list:
        pos_list.remove(pos)

    if word == '||':
        return

    word = word.strip()
    word = word.replace(' ', '_')
    # encodes the word in a way that the webpage will recognise unicode
    # must convert to lowercase to prevent hang from redirecting but leads to ignoring proper nouns and German nouns
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
                            pos_correct = True

            except KeyError:
                # item has no id attribute, do nothing
                pass
            except TypeError:
                # item has no span, do nothing
                pass

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
                        pass
                try:
                    if item.parent.name == 'td':
                        continue
                except AttributeError:
                    pass

                try:
                    if lang not in item['lang']:
                        break
                except:
                    pass

                try:
                    if 'References' in item['id']:
                        break
                except:
                    pass

                if ipa is None:
                    # finds any IPA above - hopefully from new soup
                    for i in item.find_all_previous():
                        try:
                            if i['id'] == language:
                                break
                            elif 'Pronunciation' in i['id']:
                                ipa_text = i.find_next(class_='IPA')
                                ipa = ipa_text.get_text()
                                break

                        except:
                            # no id, do nothing
                            pass

                if cat is None:
                    cat_text = item.find_next(class_='gender')
                    if cat_text is not None:
                        cat = cat_text.get_text()

                # removes citations from definition
                while soup.ul is not None:
                    soup.ul.decompose()

                if item.name == 'ol':
                    for e in item.descendants:
                        if e.name == 'li':
                            definition = e.get_text().rstrip()

                            # finds pos if unspecified
                            #if pos == '':
                            #    definition = part_of_speech + ': ' + definition
                            if num_definitions == 1:
                                break

                            definitions.append(definition)

        if ipa is None:
            ipa = ''
        if cat is None:
            cat = pos
        else:
            cat += " " + pos
        if definition is None:
            definition = ''
        if num_definitions > 1:
            definition = definitions

        word_info.append(definition)
        word_info.append(ipa)
        word_info.append(cat)
        word_info.append(scrape_audio(word, language))

    return word_info
