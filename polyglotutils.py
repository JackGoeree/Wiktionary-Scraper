from urllib.request import urlopen
import urllib.parse
from bs4 import BeautifulSoup
from gensim.corpora import WikiCorpus
import csv
import time
import os.path

'''
TODO: 
SOMEHOW, LEMMA LIST IS A NONE TYPE. SOME FUCKED UP SCOPING IS GOING ON SOMEWHERE.

- incorporate notes from individual scripts
- make a single Wiktionary page parser used by all 
- make a common read and write function for csv
- make a common progress tracker
- add time since last checkpoint
- ensure each function can be called independently, overwriting default values with parameters
- make separate functions for gender, IPA etc rather than definition scraper
- choose either ISO code or language name as only parameter - use a word_dictionary to get the other
- lemmatise, translate, define need to check if output already exists before executing

'''

start_time = time.time()
count = 0
total = 0
lemma_list = []
visited = []
# print(str(29) + str(type(lemma_list)))


def main(lang, language, overwrite='n'):

    corpus(lang, lang + '_wiki.bz2', lang + '_corpus.txt', overwrite)
    frequency(lang, lang + '_corpus.txt', overwrite)
    scrape_lemmas(lang, language, overwrite)
    inflect(lang, language, overwrite)
    # combine lemmas and inflections into a forms.csv
    lemmatise(lang, overwrite)
    translate(lang, overwrite)
    # combine _forms and _translations
    define(lang, language, overwrite)

    finish_time = time.time()
    print('Total time elapsed: ' + duration(start_time, finish_time))


def duration(start, finish):
    delta = finish - start
    elapsed = time.strftime('%H:%M:%S', time.gmtime(delta))
    elapsed_pretty = elapsed[:2] + ' hours, ' + elapsed[3:5] + ' minutes, ' + elapsed[6:8] + ' seconds.'
    return elapsed_pretty


# builds a corpus for a given language from Wikipedia dump (bz2 file)
def corpus(lang, overwrite='n', input_file=None, output_file=None):
    # Convert Wikipedia xml dump file to text corpus
    
    if output_file is None:
        input_file = lang + '_wiki.bz2'
    if output_file is None:
        output_file = lang + '_corpus.txt'
    
    if overwrite == 'n':
        try:
            if os.path.isfile(output_file):
                print(lang + '_corpus.txt found.')
                return
        except FileNotFoundError:
            # do nothing
            print(lang + '_corpus.txt not found.')

    print('Building corpus...')
    output = open(output_file, 'w', encoding='utf-8')
    wiki = WikiCorpus(input_file)

    i = 0
    for text in wiki.get_texts():
        output.write(bytes(' '.join(text), 'utf-8').decode('utf-8') + '\n')
        # output.write(bytes(' '.join(text), 'utf-8') + bytes('\n'))
        i = i + 1
        if i % 10000 == 0:
            print('Processed ' + str(i) + ' articles')
    output.close()

    print('Corpus created!')
    checkpoint = time.time()
    print('Time since start: ' + duration(start_time, checkpoint))


# creates a list of words by frequency found in input_file
def frequency(lang, overwrite='n', input_file=None, output_file=None):
    if input_file is None:
        input_file = lang + '_corpus.txt'
    if output_file is None:
        output_file = lang + '_corpus_freq.csv'
        
    if overwrite == 'n':
        try:
            if os.path.isfile(output_file):
                print(output_file + ' found.')
                return
        except FileNotFoundError:
            # do nothing
            print(output_file + ' not found.')

    # word_dict = []
    freq_list = []

    print('Building frequency list...')
    file = open(input_file, 'r', encoding='utf-8')
    if file is None:
        print('Invalid file.')
        return

    word_list = create_word_list(file)

    file.close()

    word_dict = count_frequency(word_list)

    y = 0
    for w in sorted(word_dict, key=word_dict.get, reverse=True):
        freq_row = []
        if word_dict[w] > 1:
            freq_row.append(w)
            freq_row.append(word_dict[w])
            freq_list.append(freq_row)
            if y < 20:
                # print(w, word_dict[w])
                y += 1

    with open(lang + '_corpus_freq.csv', 'w', encoding='utf-8',
              newline='') as csvW:  # change to 'a' if want to append instead of overwrite
        writer = csv.writer(csvW, delimiter=',', quotechar='@', quoting=csv.QUOTE_MINIMAL)
        # print(def_list)
        writer.writerows(freq_list)

    print('Frequency list completed!')
    checkpoint = time.time()
    print('Time since start: ' + duration(start_time, checkpoint))


def create_word_list(file):
    # print('Creating simple word list')
    # word_list = []
    string = ''
    x = 0
    for line in file:
        x += 1
        if x % 1000 == 0:
            # break
            print(x)
        string += line
    # print('File copied!')
    word_list = string.split(' ')
    return word_list


def count_frequency(word_list):
    # print('Counting frequency')
    word_dict = {}
    for word in word_list:
        if word in word_dict:
            word_dict[word] += 1
        elif word not in word_dict:
            word_dict[word] = 1
    return word_dict


def scrape_lemmas(lang, language, overwrite='n'):
    global lemma_list
    # print(str(171) + str(type(lemma_list)))
    pos_list = ['Noun', 'Verb', 'Adjective', 'Adverb', 'Preposition', 'Conjunction', 'Pronoun', 'Determiner', 'Numeral',
                'Proper_noun', 'Personal_pronoun', 'Article', 'Interjection']
    if overwrite == 'n':
        try:
            for part in pos_list:
                if os.path.isfile(lang + '_' + part.lower() + '_lemmas.csv'):
                    # print(lang + '_' + part.lower() + '_lemmas.csv found.')
                    pos_list.remove(part)
                else:
                    raise FileNotFoundError
            print('All lemma files found.')
            return
        except FileNotFoundError:
            # do nothing
            print(lang + '_' + part.lower() + '_lemmas.csv not found.')

    for part in pos_list:
        pos = part
        print('Scraping ' + pos + ' lemmas...')
        lemma_list = scrape(language, pos)
        # print(str(195) + str(type(lemma_list)))
        with open(lang + '_' + pos.lower() + '_lemmas.csv', 'w', encoding='utf-8',
                  newline='') as csvW:  # change to 'a' if want to append instead of overwrite
            writer = csv.writer(csvW, delimiter=',', quotechar='@', quoting=csv.QUOTE_MINIMAL)
            # print(def_list)
            # print(type(lemma_list))
            writer.writerows(lemma_list)
            lemma_list = []

    print('Lemma scraping completed!')
    checkpoint = time.time()
    print('Time since start: ' + duration(start_time, checkpoint))


def scrape(language, pos, url=None):
    global lemma_list
    # print(str(210) + str(type(lemma_list)))
    # visited.append(url)
    global visited

    if url is None:
        url = 'https://en.wiktionary.org/wiki/Category:' + language.replace(' ', '_') + '_' + pos.lower() + 's'

    # print(url)
    # print(visited)
    # print(url in visited)

    # print(pos)

    # print(quote_page)

    try:
        page = urlopen(url)
    except:
        print('No web page was found at ' + url)
        # print(str(221) + str(type(lemma_list)))
        return lemma_list

    soup = BeautifulSoup(page, 'html.parser')

    pages = soup.find(id='mw-pages')
    # print(pages)

    try:
        lemmas = pages.find_all(name='li')
        # print (len(lemmas))
    except AttributeError:
        # no li
        # print(str(233) + str(type(lemma_list)))
        return lemma_list

    for tag in lemmas:
        lemma_row = []
        lemma = tag.get_text()
        lemma = lemma.replace('\u200c', ' ')
        lemma_row.append(lemma)
        # lemma_row.append('')
        # print(lemma_row)
        lemma_list.append(lemma_row)
    # print(lemma_list)

    links = pages.find_all_next(title='Category:' + language.replace('_', ' ') + ' ' + pos.lower() + 's')
    # print( 'Links found: ' + str(len(links)))

    # if the url contains 'pageuntil', is the same as 'pagefrom' url already visited
    for link in links:
        # print(link['href'])
        if "until" in link['href']:
            # print("contained until")
            links.remove(link)
    try:
        if links[1] is not None:
            url = 'https://en.wiktionary.org/' + links[1]['href']
            #print(url)
            if url in visited:
                #print("already visited")
                return lemma_list
            else:
                visited.append(url)
                #print("url good, scraping")
                scrape(language, pos, url)
        else:
            return lemma_list
    except:
        # no links on page
        #print('no links')
        print(pos + ' lemmas scraped!')
        # print(str(287) + str(type(lemma_list)))
        return lemma_list
    return lemma_list


def inflect(lang, language, overwrite='n'):
    pos_list = ['Noun', 'Verb', 'Adjective', 'Adverb', 'Preposition', 'Conjunction', 'Pronoun', 'Determiner', 'Numeral',
                'Proper_noun', 'Personal_pronoun', 'Article', 'Interjection']

    if overwrite == 'n':
        try:
            for part in pos_list:
                # print(part)
                # continue
                file = lang + '_' + part.lower() + '_inflections.csv'
                # print(file)
                if os.path.isfile(file):
                    pos_list.remove(part)
                    # print(lang + '_' + part.lower() + '_inflections.csv' + ' found.')
                else:
                    # print('HEH')
                    raise FileNotFoundError
            print('All inflection files found.')
            return
        except FileNotFoundError:
            print(lang + '_' + part.lower() + '_inflections.csv not found.')

    # return

    words = []
    form_list = []
    global count
    global total
    percent = 0

    for pos in pos_list:

        print('Inflecting ' + pos.lower() + 's...')
        count = 0
        begin = time.time()
        # print(begin)
        # print('Progress:  ')
        with open(lang + '_' + pos.lower() + '_lemmas.csv', 'r',
                  encoding='utf-8') as csvR:  # change to 'a' if want to append instead of overwrite
            reader = csv.reader(csvR)
            for row in reader:
                # print(row[0])
                words.append(row[0])
        total = len(words)

        for word in words:

            if pos in pos_list:
                pos_list.remove(pos)

            # change spaces to underscores
            word = word.strip()
            word = word.replace(' ', '_')
            quote_page = 'https://en.wiktionary.org/wiki/' + urllib.parse.quote(word)
            # print('https://en.wiktionary.org/wiki/' + word)

            try:
                page = urlopen(quote_page)
            except:
                print('No web page was found at ' + quote_page)
                not_found(form_list)
                return

            soup = BeautifulSoup(page, 'html.parser')

            body = soup.find(class_='mw-parser-output')
            if body is None:
                print('Body not found')

            lang_header = body.find(id=language.replace(' ','_'))
            if lang_header is None:
                print(language + ' header not found')
                # not_found()
                continue
            pos_correct = False

            # loops through HTML following the language header
            next_section = lang_header.parent.find_all_next()
            lang_limit = None
            # found = False
            form_row = []

            if next_section is None:
                print('next_section not found')
            else:
                for item in next_section:
                    # find beginning of part of speech section
                    if not pos_correct:
                        try:
                            # print(item.span['id'])
                            if pos in item.span['id']:
                                # print(item.span['id'])
                                # print('PoS true')
                                pos_correct = True
                            # else:
                            # print(item.span['id'])
                            # print('Pos false')
                            # pos_correct = False
                        except KeyError:
                            # item has no id
                            continue
                        except TypeError:
                            # item has no span
                            pos_correct = pos_correct

                    if pos_correct:

                        # finds limit of part of speech section
                        for part in pos_list:
                            try:
                                # print(part)
                                # print(item.span['id'])
                                # print(part in item.span['id'])
                                if part in item.span['id']:
                                    # print(item.get_text() + ' is the limit')
                                    lang_limit = item
                                    # print('lang_limit is not None')
                                    break
                            except TypeError:
                                # item has no span
                                break
                            except KeyError:
                                # item has no id attribute
                                break

                        # halts execution if limit reached
                        if lang_limit is not None:
                            if item == lang_limit:
                                # print('Limit reached')
                                break  # breaks whole loop

                        try:  # find the inflection navframe
                            # print(item.name)
                            if 'NavFrame' in item['class']:
                                # print('Navframe found')
                                for element in item.descendants:
                                    if element.name == 'td':
                                        try:
                                            form = element.get_text()
                                            form = form.rstrip()
                                            form_row.append(form)
                                        except:
                                            # no text
                                            continue
                        except KeyError:
                            # item has no class attribute
                            continue

            # print(word + ': ' + str(form_row))
            # print(str(count) + "/" + str(total))
            form_list.append(form_row)
            count += 1
            # print(str(count) + "/" + str(total))
            test_limit = 10
            if count == test_limit:
                checkpoint = time.time()
                delta = checkpoint - begin
                # print("The first 10 items took " + str(delta))
                delta_unit = delta / test_limit
                # print("Each item took on average " + str(delta_unit))
                prediction = (delta_unit * total) - delta
                # print("So to finish " + str(total) + " will take " + str(prediction))
                # prediction_pretty = time.strftime('%H:%M:%S', time.gmtime(prediction))
                # print("Estimated time until completion: " + prediction_pretty[:2] + ' hours, ' + prediction_pretty[3:5]
                #       + ' minutes, ' + prediction_pretty[6:8] + ' seconds.')
                print("Estimated time of completion: " + time.strftime('%H:%M:%S', time.localtime(time.time() + prediction)))

            '''if (count / total) * 100 > percent and (count / total) * 100 % 2.5 == 0:
                percent = (count / total) * 100
                # print(str(int(percent)) + '% complete.', end='\r')
                if (count / total) * 100 % 5 == 0:
                    print(str(int(percent)) + '%|', end='\r')
                # else:
                    # print('-', end='\r')'''

        with open(lang + '_' + pos.lower() + '_inflections.csv', 'w', encoding='utf-8',
                  newline='') as csvW:  # change to 'a' if want to append instead of overwrite
            writer = csv.writer(csvW, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            writer.writerows(form_list)
        print(pos + "inflection completed!")

    print('All inflection completed!')
    checkpoint = time.time()
    print('Time since start: ' + duration(start_time, checkpoint))


# creates an empty line in output file if inflections could not be found
def not_found(form_list):
    forms = []
    i = 0
    while i < 9:
        forms.append('')
        i += 1
    form_list.append(forms)


def lemmatise(lang, overwrite='n'):
    pos_list = ['Noun', 'Verb', 'Adjective', 'Adverb', 'Preposition', 'Conjunction', 'Pronoun', 'Determiner', 'Numeral',
                'Proper_noun', 'Personal_pronoun', 'Article', 'Interjection']
    form_rows = []
    freq_words = []
    lemma_list = []
    unknown = 0
    x = 0

    with open(lang + '_corpus_freq.csv', 'r',
              encoding='utf-8') as csvR:  # change to 'a' if want to append instead of overwrite
        reader = csv.reader(csvR)
        for row in reader:
            # print(row[0])
            freq_words.append(row[0])
        # print(freq_words)
    for part in pos_list:
        with open(lang + '_' + part.lower() + '_inflections.csv', 'r',
                  encoding='utf-8') as csvR:  # change to 'a' if want to append instead of overwrite
            reader = csv.reader(csvR)
            for row in reader:
                form_rows.append(row)
                # print(row)

        for word in freq_words:
            # print(word)
            x += 1
            lemma_row = [word, 'UNKNOWN', '']
            # find in form_rows
            for row in form_rows:

                # print(row)
                # print(form_rows[1])
                for cell in row:
                    # print(cell)
                    if cell.lower() == word:
                        lemma_row[1] = row[0]
                        lemma_row[2] = row[1]
                        # lemma_list.append(lemma_row)
                        # print(lemma_row)
                        break
                if cell == word:
                    break
            #print(str(x) + '/' + str(len(freq_words)) + ' ' + str(lemma_row))
            lemma_list.append(lemma_row)
            if lemma_row[1] == 'UNKNOWN':
                unknown += 1

    with open(lang + '_freq_lemmas.csv', 'w', encoding='utf-8',
              newline='') as csvW:  # change to 'a' if want to append instead of overwrite
        writer = csv.writer(csvW, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerows(lemma_list)

    print('Lemmatisation completed!')
    print(str(unknown) + ' words could not be found')
    checkpoint = time.time()
    print('Time since start: ' + duration(start_time, checkpoint))


def translate(lang, overwrite='n'):
    # this pos needs to be extracted from relevant column in file
    pos = ''
    trans_list = []
    words = []
    pos_list = ['Noun', 'Verb', 'Adjective', 'Adverb', 'Preposition', 'Conjunction', 'Pronoun', 'Determiner', 'Numeral',
                'Proper_noun', 'Personal_pronoun', 'Article', 'Interjection']
    if pos in pos_list:
        pos_list.remove(pos)

    with open('to_translate.csv', 'r', encoding='utf-8') as csvR:
        reader = csv.reader(csvR)
        for row in reader:
            # print(row[0])
            words.append(row[0])

    for word in words:
        # print(word)
        # change spaces to underscores
        word = word.replace(' ', '_')

        quote_page = 'https://en.wiktionary.org/wiki/' + urllib.parse.quote(word)

        try:
            page = urlopen(quote_page)
        except:
            print('No web page was found at ' + quote_page + '. Did you enter a valid English word?')
            # not_found(word)
            return

        soup = BeautifulSoup(page, 'html.parser')

        body = soup.find(class_='mw-parser-output')
        if body is None:
            print('Body not found')

        english_header = body.find(id='English')
        if english_header is not None:
            print('English header found')
        pos_correct = False

        # loops through HTML following the English header
        next_section = english_header.parent.find_all_next()
        lang_limit = None
        found = False
        trans_row = []

        if next_section is None:
            print('next_section not found')
        else:
            for item in next_section:

                # find beginning of part of speech section
                if not pos_correct:
                    try:
                        # print(item.span['id'])
                        if pos in item.span['id']:
                            # print(item.span['id'])
                            print('PoS true')
                            pos_correct = True
                        # else:
                        # print(item.span['id'])
                        # print('Pos false')
                        # pos_correct = False
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
                            # print(part)
                            # print(item.span['id'])
                            # print(part in item.span['id'])
                            if part in item.span['id']:
                                print(item.get_text() + ' is the limit')
                                lang_limit = item
                                # print('lang_limit is not None')
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
                            print('Limit reached')
                            break  # breaks whole loop

                    # print('Made it')
                    # print(item)
                    try:  # find the translation navframe
                        # print(item.name)
                        if 'NavFrame' in item['class']:
                            # print('Navframe found')
                            # get the header containing the definition of the translation
                            definition = item.div.get_text()
                            # print(definition)

                            # if the target language contains a translation for that definition, extract it
                            for element in item.descendants:
                                try:
                                    if element.get('lang') is not None:
                                        if element.get('lang') == lang:
                                            target = element.get_text()
                                            # print(target)
                                            # extract all translations with their headers
                                            trans_row.append(definition + ' - ' + target)
                                            # print(trans_row)
                                            found = True
                                except AttributeError:
                                    # element has no lang attribute, do nothing
                                    continue
                    except KeyError:
                        # item has no class attribute, do nothing
                        continue

            # print(len(trans_row))
            target = None
            if not found:
                # target = GoogleTranslate(word)
                if target is None:
                    # not_found(word)
                    return
                else:
                    trans_row.append(' - ' + target)

        print(trans_row)
        trans_list.append(trans_row)

    # change to 'a' if want to append instead of overwrite
    with open(lang + '_translations.csv', 'w', encoding='utf-8', newline='') as csvW:
        writer = csv.writer(csvW, delimiter='|', quotechar='~', quoting=csv.QUOTE_MINIMAL)
        print(trans_list)
        for trans_row in trans_list:
            writer.writerow(trans_row)
            # writer.writerow([translation])

    print('Translation completed!')
    checkpoint = time.time()
    print('Time since start: ' + duration(start_time, checkpoint))


'''def GoogleTranslate(word):
    # requires langcode to be the same on wiktionary and google translate - not true for serbo-croatian and croatian
    print('Trying google translate')
    word = word.replace(' ', '_')
    translation = translator.translate(word, dest=langCode, src='en').text
    print(translation)
    return translation'''

# creates an empty line in output file if inflections could not be found
'''def not_found(word):
    print('No translation found')
    trans_row = []
    trans_row.append(word)
    trans_row.append('')
    trans_list.append(trans_row)'''


def define(lang, language, overwrite='n'):
    words = []
    pos = 'Adverb'
    pos_list = ['Noun', 'Verb', 'Adjective', 'Adverb', 'Preposition', 'Conjunction', 'Pronoun', 'Determiner', 'Numeral',
                'Proper noun',
                'Article']
    def_list = []
    def_row = []
    pos_correct = False
    ipa = None
    gender = None

    with open(lang + '_forms.csv', 'r',
              encoding='utf-8') as csvR:  # change to 'a' if want to append instead of overwrite
        reader = csv.reader(csvR)
        for row in reader:
            # print(row[0])
            words.append(row[0])

    for word in words:
        if pos in pos_list:
            pos_list.remove(pos)
            # print(pos_list)

        if word == '||':
            return

        # print(word)
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
            # not_found()
            return

        soup = BeautifulSoup(page, 'html.parser')

        # removes example sentences within definition entries - may want to extract these separately
        # must be while as each is decomposed individually
        while soup.dl is not None:
            # print('Decomposing dl')
            soup.dl.decompose()

        while soup.ul is not None:
            soup.ul.decompose()

        # print(soup.dl)

        # find the language section of the page
        lang_header = soup.find(id=language)
        if lang_header is None:
            print(language + ' header not found')
            # not_found(form_list)
            return

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
                            break
                    except:
                        x = 1

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

                            except:
                                # no id, do nothing
                                continue

                    if gender is None:
                        gender_text = item.find_next(class_='gender')
                        if gender_text is not None:
                            gender = gender_text.get_text()
                            # print(gender)

                    # print(item.get_text())
                    if item.name == 'ol':
                        # print('!')
                        for e in item.descendants:
                            if e.name == 'li':
                                definition = e.get_text().rstrip()

                                # finds pos if unspecified
                                # print (part_of_speech)
                                if pos == '':
                                    definition = part_of_speech + ': ' + definition

                                def_row.append(definition)
                            # break;

            if ipa is not None:
                def_row.insert(0, ipa)
            else:
                def_row.insert(0, '')

            if gender is not None:
                def_row.insert(0, gender)
            else:
                def_row.insert(0, '')

            # def_row.insert(0, word)
            def_list.append(def_row)
            print(word, def_row)

    with open(lang + '_definitions.csv', 'w', encoding='utf-8',
              newline='') as csvW:  # change to 'a' if want to append instead of overwrite
        writer = csv.writer(csvW, delimiter='|', quotechar='@', quoting=csv.QUOTE_MINIMAL)
        # print(def_list)
        for def_row in def_list:
            writer.writerow(def_row)

    print('Definitions completed!')
    checkpoint = time.time()
    print('Time since start: ' + duration(start_time, checkpoint))


# creates an empty line in output file if inflections could not be found
'''def not_found():
    # def_list.append(GoogleTranslate(word))
    # def_row.append(word)
    # def_list.append(def_row)
    def_row = []
    # def_row.append(word)
    print(word, def_row)
    def_list.append(def_row)


def GoogleTranslate(word):
    # requires langcode to be the same on wiktionary and google translate - not true for serbo-croatian and croatian
    print('Trying google translate')
    word = word.replace(' ', '_')
    translation = translator.translate(word, dest='en', src=langCode).text
    print(translation)
    return translation'''