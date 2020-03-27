from urllib.request import urlopen
import urllib.parse
from bs4 import BeautifulSoup
import csv
import time
import os.path

'''
TODO: 
- possible issue: inflection skips verb
- incorporate notes from individual scripts
- make a single Wiktionary page parser used by all 
- make a common read and write function for csv
- make a common progress tracker
- add time since last checkpoint - make checkpoint global so can reference value from other functions
- ensure each function can be called independently, overwriting default values with parameters
- make separate functions for gender, IPA etc rather than definition scraper
- choose either ISO code or language name as only parameter - use a word_dictionary to get the other - Tatoeba uses 
3 digit while wiktionary uses 2 digit, wikipedia uses combo
- lemmatise, translate, define need to check if output already exists before executing

'''

start_time = time.time()
count = 0
total = 0
lemma_list = []
visited = []
freq = 0
lemma = 0
# print(str(29) + str(type(lemma_list)))


def main(language, overwrite='n'):
    lang = get_language_code(language)
    # corpus(lang, lang + '_wiki.bz2', lang + '_corpus.txt', overwrite)
    frequency(lang, lang + '_corpus.txt', overwrite)
    scrape_lemmas(lang, language, overwrite)
    inflect(lang, language, overwrite) #inflects scraped lemmas
    # combine lemmas and inflections into a forms.csv
    lemmatise(lang, overwrite) #lemmatises freq words by comparing to scraped inflections
    translate(lang, overwrite)
    # combine _forms and _translations
    define(lang, language, overwrite)

    finish_time = time.time()
    print('Total time elapsed: ' + duration(start_time, finish_time))


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


def get_iso3(iso_code):
    with open('language_codes.csv', 'r', encoding='utf-8') as csvR:
        reader = csv.reader(csvR)
        for row in reader:
            if row[2] == iso_code:
                return row[6]


def duration(start, finish):
    delta = finish - start
    elapsed = time.strftime('%H:%M:%S', time.gmtime(delta))
    elapsed_pretty = elapsed[:2] + ' hours, ' + elapsed[3:5] + ' minutes, ' + elapsed[6:8] + ' seconds.'
    return elapsed_pretty


# creates a list of words by frequency found in input_file
def frequency(language, overwrite='n', input_file=None, output_file=None):
    lang = get_language_code(language)

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
            # limit the number of entries to 5000
            if len(freq_list) < 5000:
                freq_row.append(w)
                freq_row.append(word_dict[w])
                # add an example sentence to each form
                '''if lang_3 is not None:
                    freq_row.append(find_example(lang_3, w))'''
                freq_list.append(freq_row)
                if y < 20:
                    # print(w, word_dict[w])
                    y += 1
            else:
                print("Frequency row limit reached.")
                break

    with open(output_file, 'w', encoding='utf-8',
              newline='') as csvW:  # change to 'a' if want to append instead of overwrite
        writer = csv.writer(csvW, delimiter=',', quotechar='@', quoting=csv.QUOTE_MINIMAL)
        # print(def_list)
        writer.writerows(freq_list)

    print('Frequency list completed!')
    checkpoint = time.time()
    print('Time since start: ' + duration(start_time, checkpoint))

    # only call merge function if file already lemmatised
    # merge(lang, overwrite)


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


def scrape_lemmas(language, overwrite='n'):
    lang = get_language_code(language)
    language = get_language_name(lang)
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
        lemma_count = len(lemma_list)
        print(str(lemma_count) + ' ' + pos + ' lemmas scraped!')
        if lemma_count > 5000:
            print("Consider using a lemmatiser instead of the lemmatise function due to the high number of lemmas.")
        with open(lang + '_' + pos.lower() + 's.csv', 'w', encoding='utf-8',
                  newline='') as csvW:  # change to 'a' if want to append instead of overwrite
            writer = csv.writer(csvW, delimiter=',', quotechar='@', quoting=csv.QUOTE_MINIMAL)
            # print(def_list)
            # print(type(lemma_list))
            writer.writerows(lemma_list)
            lemma_list = []

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


def inflect(language, pos=None, overwrite='n', input_file=None, lemma_col=0):
    lang = get_language_code(language)
    language = get_language_name(lang)
    pos_list = ['Noun', 'Verb', 'Adjective']
    resume_point = None
    resume_row = 0

    if pos is not None:
        pos_list = [pos]
    
    if overwrite == 'n':
        try:
            for part in pos_list:
                # print(part)
                # continue
                file = lang + '_' + part.lower() + '_inflections.csv'
                # print(file)
                if os.path.isfile(file):
                    # pos_list.remove(part)
                    print(lang + '_' + part.lower() + '_inflections.csv' + ' found.')
                    
                    # open the file and check for last entry
                    with open (file, 'r', encoding='utf-8') as inflectionsCSV:
                        if input_file is None:
                            input_file = lang + '_' + part.lower() + 's.csv'
                        with open (input_file, 'r', encoding='utf-8') as lemmasCSV:
                            i = 0
                            for line in inflectionsCSV:
                                if line.strip() != "":
                                    for lemma in lemmasCSV:
                                        print(lemma.strip() + "|" + line)
                                        if lemma.strip() + "," in line:
                                            resume_lemma = lemma
                                            resume_row = i
                                            print(resume_lemma)
                                            break
                                        else:
                                            continue
                                i += 1
                    print("Last entry was " + resume_lemma + " at row " + str(resume_row))
                    break
                    
                else:
                    raise FileNotFoundError
            # print('All inflection files found.')
            # return
        except FileNotFoundError:
            print(lang + '_' + part.lower() + '_inflections.csv not found.')

    # return

    words = []
    form_list = []
    pos_break = False
    global count
    global total
    percent = 0

    if pos is not None:
        pos_break = True
        pos_param = pos

    for pos in pos_list:
        if pos_break:
            pos = pos_param
        
        if input_file is None:
            input_file = lang + '_' + pos.lower() + 's.csv'
        print('Inflecting ' + pos.lower() + 's...')
        count = 0
        begin = time.time()
        # print(begin)
        # print('Progress:  ')
        with open(input_file, 'r',
                  encoding='utf-8') as csvR:  # change to 'a' if want to append instead of overwrite
            reader = csv.reader(csvR)
            x = 0
            for row in reader:
                if x < resume_row:
                    x += 1
                    continue
                else:
                    words.append(row[lemma_col].replace("'",""))
        total = len(words)
        print(str(total) + " still to go.")

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
                print('No web page was found at https://en.wiktionary.org/wiki/' + word)
                continue

            soup = BeautifulSoup(page, 'html.parser')

            body = soup.find(class_='mw-parser-output')
            if body is None:
                print('Body not found')

            lang_header = body.find(id=language.replace(' ','_'))
            if lang_header is None:
                print(language + ' header not found for ' + word)
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

                                # limit is the next part of speech for that word and that language
                                if part in item.span['id']:
                                    lang_limit = item
                                    break
                                elif item.name == 'hr':
                                    print('The section for ' + language + " does not treat this word as a " + pos)
                                    lang_limit = item
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
                                            # span = element.span
                                            # print(span.attrs)
                                            # print(span.lang)
                                            # print(span['lang'])
                                            if element.span['lang'] == lang:
                                                try:
                                                    form = element.get_text()
                                                    form = form.rstrip()
                                                    form_row.append(form)
                                                except:
                                                    # no text
                                                    continue
                                        except:
                                            # no span
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

            with open(lang + '_' + pos.lower() + '_inflections.csv', 'a', encoding='utf-8',
                      newline='') as csvW:  # change to 'a' if want to append instead of overwrite
                writer = csv.writer(csvW, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                # writer.writerows(form_list)
                writer.writerow(form_row)
            
        # print(pos + " inflection completed at " + time.localtime(time.time()) + "!")
        if pos_break:
            break

    print('All inflections completed!')
    checkpoint = time.time()
    print('Time since start: ' + duration(start_time, checkpoint))


def lemmatise(language, overwrite='n'):
    lang = get_language_code(language)
    pos_list = ['Noun', 'Verb', 'Adjective']
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


def translate(word, language, pos=None):
    lang = get_language_code(language)
    translation = None
    pos_list = ['Noun', 'Verb', 'Adjective', 'Adverb', 'Preposition', 'Conjunction', 'Pronoun', 'Determiner', 'Numeral',
                'Proper_noun', 'Personal_pronoun', 'Article', 'Interjection']
    if pos in pos_list:
        pos_list.remove(pos)

    # print(word)
    # change spaces to underscores
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
                            # print(item.get_text() + ' is the limit')
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
                        # print('Limit reached')
                        break  # breaks whole loop

                # print('Made it')
                # print(item)
                try:  # find the translation navframe
                    # print(item.name)
                    if 'NavFrame' in item['class']:
                        # print('Navframe found')
                        # print(item)
                        # get the header containing the definition of the translation
                        definition = item.div.get_text()
                        # print(definition)

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
                                        # print(target)
                                        # extract all translations with their headers
                                        trans_row.append(definition + ' - ' + translation)
                                        # print(trans_row)
                                        found = True
                            except AttributeError:
                                # element has no lang attribute, do nothing
                                continue
                        if translation is not None:
                            break

                except KeyError:
                    # item has no class attribute, do nothing
                    continue

        # print(len(trans_row))
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
                                    # print(item.get_text() + ' is the limit')
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
                                # print('Limit reached')
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
                                                translation = element.get_text()
                                                # print(target)
                                                # extract all translations with their headers
                                                trans_row.append(definition + ' - ' + translation)
                                                # print(trans_row)
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

    '''# change to 'a' if want to append instead of overwrite
    with open(lang + '_translations.csv', 'w', encoding='utf-8', newline='') as csvW:
        writer = csv.writer(csvW, delimiter='|', quotechar='~', quoting=csv.QUOTE_MINIMAL)
        print(trans_list)
        for trans_row in trans_list:
            writer.writerow(trans_row)
            # writer.writerow([translation])

    print('Translation completed!')
    checkpoint = time.time()
    print('Time since start: ' + duration(start_time, checkpoint))'''



def translate_file(language, overwrite='n'):
    lang = get_language_code(language)
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
            continue

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

# runs successfully for first 20 words or so, then fails to find ipa
def scrape_ipa_list(language, overwrite='n', input_file=None, pos=None, lemma_col=0):
    lang = get_language_code(language)
    language = get_language_name(lang)
    words = []
    ipa_row = []
    ipa_list = []
    pos_list = ['Noun', 'Verb', 'Adjective', 'Adverb', 'Preposition', 'Conjunction', 'Pronoun', 'Determiner', 'Numeral',
                'Proper noun', 'Article']
    pos_correct = False
    ipa = None

    if input_file is None:
        input_file = lang + "_sketch.csv"

    with open(input_file, 'r',
              encoding='utf-8') as csvR:  # change to 'a' if want to append instead of overwrite
        reader = csv.reader(csvR)
        for row in reader:
            # print(row[0])
            words.append(row[lemma_col])

    for word in words:
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
            continue

        soup = BeautifulSoup(page, 'html.parser')

        # find the language section of the page
        lang_header = soup.find(id=language)
        if lang_header is None:
            print(language + ' header not found')
            continue

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
                            print('Different language encountered')
                            break
                    except:
                        x = 1

                    try:
                        if 'References' in item['id']:
                            print ('References encountered')
                            break
                    except:
                        x = 1

                    #print ('survived')

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


        ipa_row.append(word)
        if ipa is not None:
            ipa_row.insert(0, ipa)
        else:
            ipa_row.insert(0, '')

        # def_row.insert(0, word)
        ipa_list.append(ipa_row)
        print(word, ipa_row)

    with open(lang + '_ipa.csv', 'w', encoding='utf-8',
              newline='') as csvW:  # change to 'a' if want to append instead of overwrite
        writer = csv.writer(csvW, delimiter='|', quotechar='@', quoting=csv.QUOTE_MINIMAL)
        # print(def_list)
        for ipa_row in ipa_list:
            writer.writerow(ipa_row)

    print('Definitions completed!')
    checkpoint = time.time()
    print('Time since start: ' + duration(start_time, checkpoint))


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
    cat_row = []
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

        cat_row.append(word)
        if cat is not None:
            cat_row.append(cat)
        else:
            cat_row.append('')

    return cat_row


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

        ipa_row.append(ipa)
        ipa_row.append(cat)
        ipa_row.append(definition)

    return ipa_row


def define(word, language, pos=None):
    lang = get_language_code(language)
    language = get_language_name(lang)
    words = []
    pos_list = ['Noun', 'Verb', 'Adjective', 'Adverb', 'Preposition', 'Conjunction', 'Pronoun', 'Determiner', 'Numeral',
                'Proper noun', 'Article']
    def_list = []
    def_row = []
    definitions = []
    pos_correct = False

    def_row = []
    definitions = []
    if pos in pos_list:
        pos_list.remove(pos)
        # print(pos_list)

    if word == '||':
        return ''

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
        return ''

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

                            definitions.append(definition)
                        # break;

        return definitions
        # print(word, definitions)


def define_file(language, overwrite='n', input_file=None, pos=None, lemma_col=0):
    lang = get_language_code(language)
    language = get_language_name(lang)
    words = []
    pos_list = ['Noun', 'Verb', 'Adjective', 'Adverb', 'Preposition', 'Conjunction', 'Pronoun', 'Determiner', 'Numeral',
                'Proper noun', 'Article']
    def_list = []
    def_row = []
    definitions = []
    pos_correct = False

    if input_file is None:
        input_file = lang + "_sketch.csv"

    with open(input_file, 'r',
              encoding='utf-8') as csvR:  # change to 'a' if want to append instead of overwrite
        reader = csv.reader(csvR)
        for row in reader:
            # print(row[0])
            words.append(row[lemma_col])

    for word in words:
        def_row = []
        definitions = []
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
            continue

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
            continue

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

                                definitions.append(definition)
                            # break;

            def_list.append(definitions)
            print(word, definitions)

    with open(lang + '_definitions.csv', 'w', encoding='utf-8',
              newline='') as csvW:  # change to 'a' if want to append instead of overwrite
        writer = csv.writer(csvW, delimiter='|', quotechar='@', quoting=csv.QUOTE_MINIMAL)
        # print(def_list)
        for def_row in def_list:
            writer.writerow(def_row)

    print('Definitions completed!')
    checkpoint = time.time()
    print('Time since start: ' + duration(start_time, checkpoint))


# lemma must be first column, freqs second
def merge(language, overwrite='n', input_file=None, freq_col=1, lemma_col=0):
    lang = get_language_code(language)
    # print("Merging duplicates...")
    freq_list = []
    global freq
    global lemma
    freq = freq_col
    lemma = lemma_col

    if overwrite == 'n':
        return
    if input_file is None:
        input_file = lang + "_corpus_freq.csv"

    with open(input_file, 'r', encoding='utf-8') as csvR:
        reader = csv.reader(csvR)
        for row in reader:
            # print(row[0])
            freq_list.append(row)

    print("Alphabetising...")
    alpha_freqs = sorted(freq_list, key=sort_by_lemma)

    # convert freqs to int rather than str
    for row in alpha_freqs:
        row[freq_col] = row[freq_col].replace("'", "")
        row[freq_col] = int(float((row[freq_col])))

    x = 0
    try:
        while x < len(alpha_freqs):
            current_lemma = alpha_freqs[x][lemma_col]
            next_lemma = alpha_freqs[x+1][lemma_col]
            # if duplicate, merge frequency counts
            while current_lemma == next_lemma:
                # print("Duplicate found.")
                current_freq = int(alpha_freqs[x][freq_col])
                next_freq = int(alpha_freqs[x+1][freq_col])
                '''print(alpha_freqs[x+1][lemma_col] + " has the same lemma as " + alpha_freqs[x][lemma_col] + ". By adding " +
                str(current_freq) + " and " + str(next_freq) + " the new total is " + str(current_freq + next_freq))'''
                current_freq += next_freq
                alpha_freqs[x][freq_col] = current_freq
                alpha_freqs.pop(x+1)
                next_lemma = alpha_freqs[x + 1][lemma_col]
            x += 1
    except IndexError:
        # reached end of list
        x = 0

    # sort by frequency again
    unique_freqs = sorted(alpha_freqs, key=sort_by_freq, reverse=True)
    print(unique_freqs[:10])

    with open(input_file, 'w', encoding='utf-8', newline='') as csvW:
        writer = csv.writer(csvW, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerows(unique_freqs)

    checkpoint = time.time()
    print('Time since start: ' + duration(start_time, checkpoint))


def sort_by_freq(elem):
    global freq
    return elem[freq]


def sort_by_lemma(elem):
    global lemma
    return elem[lemma]


def download_word_audio(language, word, overwrite="n"):
    lang = get_language_code(language)
    if overwrite == 'n':
        try:
            file = lang + "_" + word + '.ogg'
            if not os.path.isfile(file):
                raise FileNotFoundError
            return
        except FileNotFoundError:
            x = 1
            #print(lang + "_" + word + '.ogg' + ' not found, commencing download...')

    word = word.replace(" ", "_");
    try:
        url = "https://commons.wikimedia.org/wiki/File:" + lang + "-" + urllib.parse.quote(word) + ".ogg"
        # print(url)
        page = urlopen(url)
    except urllib.error.HTTPError:
        print(word + " has no audio.")
        return

    soup = BeautifulSoup(page, 'html.parser')
    # print(soup)
    link = soup.find(class_="internal")
    # print(link)
    ogg_url = link['href']
    # print(ogg_url)

    try:
        ogg = urlopen(ogg_url)
    except urllib.error.HTTPError:
        print(word + " has no audio.")
        return

    with open(get_iso3(lang) + "_" + word + '.ogg', 'wb') as file:
        file.write(ogg.read())


'''def find_sentences(lang, word):
    file = open(lang + "_corpus.txt", 'w', encoding='utf-8')
    string = ''
    x = 0
    for line in file:
        x += 1
        if x % 1000 == 0:
            # break
            print(x)
        string += line

    sentence_list = string.split(".")
    sentences = []

    for sentence in sentence_list:
        if word in sentence:
            sentences.append(sentence)

    print(sentences)'''


def find_example(language, lemma):
    lang = get_language_code(language)
    examples = []
    file = open(lang + "_raw.txt", 'r', encoding='utf-8')
    with open(lang + "_examples.csv", "w", encoding='utf-8') as csvW: 
        writer = csv.writer(csvW, delimiter=',', quotechar='@', quoting=csv.QUOTE_MINIMAL)
        for line in file:
            #prevent merely looking for the sequence of letters as opposed to the word eg 'kto' = 'nitko'
            if " " + lemma + " " in line:
                #print (line)
                exampleRow = []
                exampleRow.append(line) #remove new line first
                # translation = google_translate(line, get_iso2(lang))
                # exampleRow.append(translation)
                examples.append(exampleRow)
                print(exampleRow)
                
            # elif at start of line, end of line or preceded/followed by punctuation
        for row in examples:
            writer.writerow (row)
                
    file.close()
