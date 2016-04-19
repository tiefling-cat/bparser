#! /usr/bin/python3
import re, random, os, shutil

babfname = 'babenko.fb2'
outfolder = 'goodies'
if not os.path.exists(outfolder):
    os.mkdir(outfolder)
catfname = os.path.join(outfolder, 'cats.txt')
testfname = os.path.join(outfolder, 'test.csv')
errorfname = os.path.join(outfolder, 'errors.txt')
statfname = os.path.join(outfolder, 'stats.txt')
aspprefname = os.path.join(outfolder, 'asp_pre.csv')
synsetsfname = os.path.join(outfolder, 'synsets.txt')
neo4j_synsets_fname = os.path.join(outfolder, 'neo4j_synsets.csv')
neo4j_syn_ties_fname = os.path.join(outfolder, 'neo4j_syn_ties.csv')
neo4j_asp_ties_fname = os.path.join(outfolder, 'neo4j_asp_ties.csv')
neo4j_titles_fname = os.path.join(outfolder, 'neo4j_titles.csv')
neo4j_title_ties_fname = os.path.join(outfolder, 'neo4j_title_ties.csv')

aspdouble = "двувидовой"
asppair = "аспектуальная пара"
aspperf = "совершенный"
aspimpf = "несовершенный"
innerdelim = ", "
stylere = r"<emphasis>((разг.)|(груб.)|(пренебр.)|(офиц.)|(устар.)|(спец.)|(презр.)|(шутл.)|(ирон.)|(неодобр.)|(книжн.)|(высок.)|(трад.-поэт.))\s</emphasis>"
aspdoublere = r"<emphasis>несов. </emphasis>и <emphasis>сов. </emphasis>"
aspperfre = r"<emphasis>сов. </emphasis>"
checkre = r"^([а-яё-]*)((чь)|(ть)|(ти))((сь)|(ся))?$"

#styles = {'разг.': 1776, 'груб.': 2, 'пренебр.': 4, 'офиц.': 7, 'устар.': 130, 'спец.': 20, 'презр.': 1, 'шутл.': 2, 'безл.': 2, 'ирон.': 5, 'неодобр.': 7, 'книжн.': 139, 'высок.': 57}
def minestyles(synsets):
    """
    Find all marks pretending to be about style and count their frequencies.
    """
    styles = []
    for synset in synsets:
        for word in synset.synonyms:
            if word.style != None:
                styles.append(word.style)
    stylefreqs = {}
    for item in styles:
        stylefreqs[item] = stylefreqs.get(item, 0) + 1
    return stylefreqs

def chopchunks(text):
    chunks = []
    print ("Chopping raw text into chunks.")    
    for match in re.finditer (r"<emphasis><strong>Глаголы\s</strong></emphasis>(.*?)(([0-9]+?\.)|(Наречия)|(Союзы)|(Предлоги)|(Частицы)|(Речевые))", text):
        chunk = Chunk (re.sub(r"^</p>", "", match.group(1)), match.start())
        chunks.append (chunk)
    chunks.pop(0)
    print ("Got", len(chunks), "chunks.\n")
    return chunks

def chunkbyoffset(chunks, offset, flag):
    ch = -1    
    for i in range(len(chunks)):
        if chunks[i].start == offset:
            ch = i
            break
    if ch < 0:
        print ("No chunk found.")
    elif flag == -1:
        print ("Previous chunk:")
        chunks[ch-1].output()
    elif flag == 1:
        print ("Next chunk:")
        chunks[ch+1].output()
    else:
        print ("The chunk:")
        chunks[i].output()

def synsetsbyoffset(synsetlist, offset):
    for synset in synsetlist.list:
        if synset.start == offset:
            synset.output()
        
class Chunk:
    """
    The class represents a chunk of raw text that contains all synsets in a bottom class.
    """
    def __init__(self, text, start):
        self.text = text
        self.start = start

    def parsechunk(self):
        word = r"[А-ЯЁ']{2,}"
        part = word + r"(?:\sи\s" + word + ")?"
        first = part + r"(?:/" + part + r")?.*?"
        second = r"[А-Я][^А-ЯЁ]*?(?:(?:и т.д.\)?)|(?:и т.п.\)?)|(?:(?<!(?:(?:.. т)|(?:.. ф)|(?:.н.п)|(?: Вин)|(?:. мн)|(?:...ч)))\.))"
        synsets = []

        regex = "(" + first + second + ")"
        parts = re.findall(regex, self.text)
        for part in parts:
            regex = "(" + first + ")" + second
            match = re.search(regex, part)
            if match:
                part1 = match.group(1)
            else:
                part1 = ""
            regex = first + "(" + second + ")"
            match = re.search(regex, part)
            if match:
                part2 = match.group(1)
            else:
                part2 = ""
            synset = Synset(part1, part2, part, self.start)
            synsets.append(synset)
        return synsets

    def output(self):
        print (self.text, self.start, "\n")

#class Lemma:
#    """The class represents one lemma.
#    """
#    def __init__(self, text):
#        self.lemma 

class Word:
    """
    The class represents one word meaning.
    """
    def __init__(self, text=None):
        """
        Get a text for one word, parse it, and initialize a word meaning with it.
        """
        self.asp = None
        self.style = None
        self.constr = None
        self.stress = None
        self.asplemma = None
        self.asplemmastress = None
        self.id = None
        self.asppair = None
        
        if text:
            asp = re.search(aspdoublere, text)
            if asp:
                text = re.sub(aspdoublere, "", text)
                self.setasp(aspdouble)
            else:
                asp = re.search(aspperfre, text)
                if asp:
                    text = re.sub(aspperfre, "", text)
                    self.setasp(aspperf)                
            
            style = re.search(stylere, text)
            if style:
                text = re.sub(stylere, "", text)
                self.setstyle(style.group(1))
        
            constrlist = re.findall(r"<emphasis>(.*?)\s</emphasis>", text)
            if constrlist != []:
                text = re.sub(r"<emphasis>(.*)\s</emphasis>", "", text)
                for constr in constrlist:    
                    self.setconstr(constr.rstrip(r"\."))

            lemma = text.rstrip(r" <>/p\.").lower()
            asplemma = re.search(r"([а-яё' -]+)/\s?([а-яё' -]+)", lemma)
            if not asplemma:
                self.lemma = lemma
            else:
                self.setasp(asppair)
                self.lemma = asplemma.group(1)
                self.asplemma = asplemma.group(2)
        
            stresspos, stressreplace = self.findstress(self.lemma)
            if stresspos:
                self.stress = stresspos
                if stressreplace:
                    self.lemma = re.sub("'", "", self.lemma)

            if self.asplemma:
                stresspos, stressreplace = self.findstress(self.asplemma)
                if stresspos:
                    self.asplemmastress = stresspos
                    if stressreplace:
                        self.asplemma = re.sub("'", "", self.asplemma)

    def __repr__(self):
        out = "lemma = " + self.lemma
        if self.stress:
            out = out + ", stress = " + str(self.stress)
        if self.asplemma:
            out = out + ", asplemma = " + self.asplemma
        if self.asplemmastress:
            out = out + ", asplemmastress = " + str(self.asplemmastress)
        if self.constr:
            out = out + ", constr = " + self.constr
        if self.asp:
            out = out + ", asp = " + self.asp
        if self.style:
            out = out + ", style = " + self.style
        if self.asppair:
            out = out + ", asppair = " + self.asppair
        return out 

    def findstress(self, lemma):
        stress = re.search("'", lemma)
        if stress:
            return stress.start(), True
        stress = re.search("ё", lemma)
        if stress:
            return stress.start() + 1, False
        stress = re.search("[аеиоуыэюя]", lemma)
        if stress:
            return stress.start() + 1, False
        return None, False

    def setstyle(self, style):
        if not self.style:
            self.style = style
        else:
            self.style = self.style + innerdelim + style

    def setconstr(self, constr):
        if not self.constr:
            self.constr = constr
        else:
            self.constr = self.constr + innerdelim + constr

    def setasp(self, asp):
        if not self.asp:
            self.asp = asp
        else:
            self.asp = self.asp + innerdelim + asp

    def setid(self, global_id):
        self.id = global_id
        return global_id + 1

    def output(self):
        print (self)

    def txtout(self, txtfile):
        txtfile.write(self.__repr__() + "\n")

    def to_neo4j_csv(self, csvout, definition):
        out = '"' + str(self.id) + '","' + self.lemma + '","'
        if self.stress:
            out = out + str(self.stress)
        out = out + '","'
        if self.asplemma:
            out = out + self.asplemma
        out = out + '","'
        if self.asplemmastress:
            out = out + str(self.asplemmastress)
        out = out + '","'
        if self.asp:
            out = out + self.asp
        out = out + '","'
        if self.style:
            out = out + self.style
        out = out + '","'
        out = out + definition + '","'
        if self.constr:
            out = out + self.constr
        out = out + '"\n'
        csvout.write(out)

class SynsetList:
    """
    The class represents a list of synsets.
    """
    def __init__(self, initlist):
        self.list = initlist

    def __repr__(self):
        return '\n'.join([synset.__repr__() for synset in self.list])

    def add(self, synset):
        self.list.append(synset)
    
    def addlist(self, synsets):
        self.list.extend(synsets)

    def length(self):
        return len(self.list)

    def setids(self, global_id):
        for synset in self.list:
            global_id = synset.setids(global_id)
        return global_id

    def output(self, raw=False):
        for synset in self.list:
            synset.output(raw)

    def csvout(self, csvfile):
        for i, synset in enumerate(self.list):
            synset.csvout(csvfile, i)

    def txtout(self, txtfile, randflag, dbgflag):
        for synset in self.list:
            synset.txtout(txtfile, randflag, dbgflag)

    def countsyns(self):
        syncount = 0
        for synset in self.list:
            syncount += synset.countsyns()
        return syncount

    def getrandsynsets(self, count):
        randsynsets = SynsetList(random.sample(self.list, count))
        return randsynsets

    def checkverbs(self):
        nonverbs = SynsetList([])
        clean_list = []       
        for synset in self.list:
            search = synset.checkverbs()            
            if search:
                nonverbs.add(synset)
            else:
                clean_list.append(synset)
        self.list = clean_list
        return nonverbs

    def bycategory(self, category):
        return SynsetList([synset for synset in self.list if synset.category.text == category])

    def to_neo4j_csv(self, csvout):
        for synset in self.list:
            synset.to_neo4j_csv(csvout)

    def syns_to_neo4j_csv(self, synscsvout, aspcsvout):
        for synset in self.list:
            synset.syns_to_neo4j_csv(synscsvout, aspcsvout)

    def asp_expls_out(self, ofile):
        for synset in self.list:
            synset.asp_expls_out(ofile)

    def lemma_count(self):
        verb_list = []
        for synset in self.list:
            for word in synset.synonyms:
                verb_list.append(word.lemma)
        return len(list(set(verb_list)))

class Synset:
    """
    The class represents a synset.

    synonyms: The list of synonyms (of class Word). The first word in each synset is the dominant designated by Babenko.
    definition: Naturally, the definition of the synset from Babenko.
    synsinrow: Unparsed string of the synonyms.
    start: Offset of the synset in the raw text.
    category: The bottom category for the synset (of class Title).
    """
    def __init__(self, part1="", part2="", raw="", start=0):
        self.synsinrow = part1
        self.raw = raw
        self.definition = part2.rstrip(r"\.") + "."
        self.start = start
        self.category = None # We determine it later.

        # Parse synonyms, make synonyms list.
        syns = part1.split(", ")
        self.synonyms = []        
        for syn in syns:
            word = Word(syn)
            self.synonyms.append(word)

        self.recheck() # Some technomagic here.
        self.checkasp() # More technomagic for the techno god!

    def __repr__(self):
        out_str = 'def = {}\n'.format(self.definition)
        if self.category:
            out_str = out_str + 'category = {} {}\n'.format(self.category.num, self.category.text)
        out_str = out_str + '\n'.join([synonym.__repr__() for synonym in self.synonyms]) + '\n'
        return out_str

    def recheck(self):
        """
        Huge crutch.
        """
        killlist = []
        newsyns = []
        length = len(self.synonyms)
        for i in range(length-1):
            if self.synonyms[i].lemma == "":
                if self.synonyms[i].style:
                    killlist.append(i)
                    offset = 1
                    while i + offset < length and self.synonyms[i+offset].lemma == "":
                        offset += 1
                    if i + offset < length:
                        self.synonyms[i+offset].setstyle(self.synonyms[i].style)
                if self.synonyms[i].asp:
                    killlist.append(i)
                    offset = 1
                    while i + offset < length and self.synonyms[i+offset].lemma == "":
                        offset += 1
                    if i + offset < length:
                        self.synonyms[i+offset].setasp(self.synonyms[i].asp)
                if self.synonyms[i].constr:
                    killlist.append(i)
                    offset = -1
                    while i + offset >= 0 and self.synonyms[i+offset].lemma == "":
                        offset -= 1
                    if i + offset >= 0:
                        self.synonyms[i+offset].setconstr(self.synonyms[i].constr)

        last = len(self.synonyms) - 1 
        if (self.synonyms[last].lemma == "") and (self.synonyms[last].constr):
            killlist.append(last)
            offset = -1
            while last + offset >= 0 and self.synonyms[last+offset].lemma == "":
                offset -= 1
                if last + offset >= 0:
                    self.synonyms[last+offset].setconstr(self.synonyms[last].constr)

        for i in range(len(self.synonyms)):
            if i not in killlist:
                newsyns.append(self.synonyms[i])
        self.synonyms = newsyns

        for synonym in self.synonyms:
            constrfrag = re.search(r"[а-яё-]+?\s([а-яё]+)", synonym.lemma)
            if constrfrag:
                if synonym.constr:
                    synonym.constr = constrfrag.group(1) + " " + synonym.constr
                    synonym.lemma = re.sub(r"\s" + constrfrag.group(1), "", synonym.lemma)

    def checkasp(self):
        newsyns = []
        for syn in self.synonyms:
            if not syn.asp:
                syn.asp = aspimpf
                newsyns.append(syn)
            elif syn.asp == aspperf or syn.asp == aspdouble:
                newsyns.append(syn)
            elif syn.asp == asppair:
                syn.asp = aspimpf
                newasps = syn.asplemma.split(" и ")
                syn.asplemma = None
                aspstress = syn.asplemmastress
                syn.asplemmastress = None
                newsyns.append(syn)
                for newasp in newasps:
                    neword = Word()
                    neword.lemma = newasp
                    neword.asp = aspperf
                    neword.stress = aspstress
                    neword.asppair = syn.lemma
                    newsyns.append(neword)
        self.synonyms = newsyns

    def setcategory(self, category):
        self.category = category

    def countsyns(self):
        """
        Count total word meanings in synset.
        """
        count = 0
        for syn in self.synonyms:
            if syn.asp == asppair or syn.asp == aspdouble:
                count += 2 # Aspect pairs and dual aspect verbs count as two meanings.
            else:
                count += 1
        return count

    def output(self, raw):
        print ("def =", self.definition)
        if self.category:
            print ("category =", self.category.num, self.category.text)
        #print (re.sub(r"</emphasis>", "", re.sub("<emphasis>", "", re.sub(r" </emphasis>,", ",", self.synsinrow))))
        for synonym in self.synonyms:
            synonym.output()
        if raw:
            print (self.raw)
        print()
        #print ("start =", self.start, "\n")

    def csvout(self, csvfile, num):
        syns = self.synonyms
        random.shuffle(syns)
        for syn in syns:
            if syn.lemma != "":
                output.append(';'.join([str(num), str(syn.id), syn.lemma, str(syn.stress), syn.asp, syn.style, syn.constr)
        csvfile.write('\n'.join(output))

    def txtout(self, txtfile, randflag, dbgflag):
        txtfile.write("def = " + self.definition + "\n")
        if self.category:
            txtfile.write("category = " + self.category.num + " " + self.category.text + "\n")
        syns = self.synonyms
        if randflag:
            random.shuffle(syns)
        for synonym in syns:
            synonym.txtout(txtfile)
        if dbgflag:
            txtfile.write("raw = " + self.raw + "\n")
        txtfile.write("\n")

    def checkverbs(self):
        for word in self.synonyms:
            match = re.match(checkre, word.lemma)
            if not match:
                return True
            if word.asplemma:
                match = re.match(checkre, word.asplemma)
                if not match:
                    return True
        return False

    def setids(self, global_id):
        for word in self.synonyms:
            global_id = word.setid(global_id)
        return global_id

    def to_neo4j_csv(self, csvout):
        for word in self.synonyms:
            word.to_neo4j_csv(csvout, self.definition)

    def syns_to_neo4j_csv(self, syncsvout, aspcsvout):
        head_id = self.synonyms[0].id
        for leaf in self.synonyms[1:]:
            if leaf.asppair:
                head_cand_id = None
                for head_cand in self.synonyms:
                    if head_cand.lemma == leaf.asppair:
                        head_cand_id = head_cand.id
                if head_id:
                    aspcsvout.write('"{}","{}"\n'.format(str(head_cand_id), str(leaf.id)))
            else:
                syncsvout.write('"{}","{}"\n'.format(str(head_id), str(leaf.id)))

    def asp_expls_out(self, ofile):
        for syn in self.synonyms:
            ofile.write("{},{}\n".format(syn.lemma, syn.asp))

class TitleList:
    """
    The class represents a list of semantic classes.
    """
    def __init__(self, text):        
        print ("Making a tree of semantic classes.")
        self.list = []
        self.findall(text)
        self.markbottoms()
        #self.output()
        print("Got {} semantic classes of all levels.\n".format(len(self.list)))
        #self.txtout()

    def findall(self, text):
        for match in re.finditer(r"<p>(([0-9]+\.)+.*?)</p>", text):
            title = Title(match.group(1), match.start())
            self.list.append(title)

    def markbottoms(self):
        for i in range(len(self.list)-1):
            if self.list[i].level >= self.list[i+1].level:
                self.list[i].setbottom()
        self.list[len(self.list)-1].setbottom()

    def length(self):
        return len(self.list)
    
    def output(self):
        for title in self.list:
            title.output()
        print(len(self.list), "semantic classes total.\n")

    def txtout(self):
        with open (catfname, "w", encoding="utf-8") as catfile:
            count = 0
            for title in self.list:
                if not title.bottom or title.synset_count > 0:
                    title.txtout(catfile)
                    count += 1
            catfile.write("\n" + str(len(self.list)) + " non-empty categories of all levels total.\n")

    def to_neo4j_csv(self, csvout):
        for title in self.list:
            csvout.write('"' + title.num + '","' + title.text + '"\n')

class Title:
    """
    The class represents a semantic class.

    num: Class number in the text, e.g., 1.3.2.
    text: Class name.
    start: Offset in the raw text.
    level: Level of the class in the tree.
    bottom: True if the class is the lowest, False otherwise.
    """
    def __init__(self, text, start):
        self.bottom = False # We evaluate it later.
        self.start = start
        self.num = None

        num = re.match(r"([0-9.]+)\s", text)
        if num:
            text = re.sub(r"[0-9.]+\s", "", text)
            self.num = num.group(1)

        self.text = text

        # Count level by the number of dots in num.
        self.level = len(re.findall(r"\.", self.num))
        self.synset_count = None

    def __repr__(self):
        return ' '.join([self.num, self.text, str(self.start), str(self.level), str(self.bottom), str(self.synset_count)])  + "\n"
    
    def setbottom(self):
        self.bottom = True

    def output(self):
        print (self.num, self.text, self.start, self.level, self.bottom, self.synset_count)
    
    def txtout(self, outfile):
        #outfile.write(self.num + " " + self.text + ", " + str(self.start) + ", " + str(self.level) + ", " + str(self.bottom) + "\n")
        if self.bottom:
            outfile.write(' '.join([self.num, self.text, str(self.synset_count)]) + "\n")
        else:
            outfile.write(' '.join([self.num, self.text]) + "\n")

def marksynsets(synsets, titles):
    i = j = 0
    while j < titles.length() - 1 and i < synsets.length():
        #while not titles.list[j].bottom and j < titles.length() - 1:
        #    j += 1
        titles.list[j].synset_count = 0
        while i < synsets.length() and synsets.list[i].start < titles.list[j+1].start:
            synsets.list[i].setcategory(titles.list[j])
            titles.list[j].synset_count += 1
            i += 1
        j += 1
    titles.list[j].synset_count = 0
    while i < synsets.length():
        titles.list[j].synset_count += 1
        synsets.list[i].setcategory(titles.list[j])
        i += 1

def randsynsets(synsets, count):
    randsynsets = synsets.getrandsynsets(10)
    randsynsets.output()
    #with open(testfname, "w", encoding="utf-8") as csvfile:
    #    randsynsets.csvout(csvfile)

def check(synsets):
    nonverbs = synsets.checkverbs()
    print ("Synsets with errors found:\n")    
    nonverbs.output(True)
    print ("Messed up", nonverbs.length(), "times.")
    with open(errorfname, "w", encoding="utf-8") as errorfile:
        nonverbs.txtout(errorfile, False, True)
        errorfile.write("Messed up " + str(nonverbs.length()) + " times.")

def getstats(synsets, titles):
    with open(statfname, "w", encoding="utf-8") as statfile:
        statfile.write(str(titles.length()) + " categories total.\n")
        statfile.write(str(synsets.countsyns()) + " words in " + str(synsets.length()) + " synsets found.")    

def tietitles(synsets, titles):
    with open(neo4j_title_ties_fname, "w", encoding = "utf-8") as neo4jout:
        neo4jout.write('"title_num","head_id"\n')        
        for title in titles.list:
            synsbytitle = synsets.bycategory(title.text)
            for synset in synsbytitle.list:
                neo4jout.write('"' + title.num + '","' + str(synset.synonyms[0].id) + '"\n')

def neo4jout(synsets):
    with open(neo4j_synsets_fname, "w", encoding = "utf-8") as neo4jout:
        neo4jout.write('"id","lemma","stress","asplemma","asplemmastress","asp","style","def","constr"\n')
        synsets.to_neo4j_csv(neo4jout)

    synneo4jout = open(neo4j_syn_ties_fname, "w", encoding = "utf-8")
    aspneo4jout = open(neo4j_asp_ties_fname, "w", encoding = "utf-8")
    synneo4jout.write('"head_id","leaf_id"\n')
    aspneo4jout.write('"head_id","leaf_id"\n')
    synsets.syns_to_neo4j_csv(synneo4jout, aspneo4jout)
    synneo4jout.close()
    aspneo4jout.close()

    with open(neo4j_titles_fname, "w", encoding = "utf-8") as neo4jout:
        neo4jout.write('"num","text"\n')
        titles.to_neo4j_csv(neo4jout)
    tietitles(synsets, titles)

def aspsout(synsets):
    with open(aspprefname, "w", encoding = "utf-8") as ofile:
        ofile.write("lemma,aspect\n")
        synsets.asp_expls_out(ofile)

def parse_babenko(check_em=False):
    if os.path.exists(outfolder):
        shutil.rmtree(outfolder)
    os.mkdir(outfolder)

    with open(babfname, "r", encoding="utf-8") as infile:
        fulltext = infile.read().replace("&#769; ", "'").replace(" &#769;", "'").replace("&#769;", "'")

    titles = TitleList(fulltext)
    chunks = chopchunks(fulltext)

    print ("Making a list of synsets.")
    synsets = SynsetList([])
    for chunk in chunks:
        synsets.addlist(chunk.parsechunk())
    marksynsets(synsets, titles)
    titles.txtout()
    print("Got {} synsets.\n".format(synsets.length())) 

    if check_em:
        check(synsets)

    with open(synsetsfname, "w", encoding="utf-8") as txtfile:
        synsets.txtout(txtfile, False, False)
    getstats(synsets, titles)

    print("Got {} words meanings total.".format(synsets.setids(0)))

    return titles, synsets, chunks

if __name__ == "__main__":
    titles, synsets, chunks = parse_babenko()
    #neo4jout(synsets)
    #aspsout(synsets)
