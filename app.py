from flask import Flask, request, jsonify, render_template_string
import random
import os
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ----------------------------------------------------------------------------
# GAME 1: NUMBER QUEST  (upgraded number-guessing game)
# ----------------------------------------------------------------------------

DIFFICULTIES = {
    'easy':   {'min': 1, 'max': 50,  'attempts': 8,  'label': 'Easy (1-50)'},
    'medium': {'min': 1, 'max': 100, 'attempts': 10, 'label': 'Medium (1-100)'},
    'hard':   {'min': 1, 'max': 300, 'attempts': 12, 'label': 'Hard (1-300)'},
}


class NumberGame:
    def __init__(self):
        self.secret_number = None
        self.attempts = 0
        self.max_attempts = 10
        self.game_over = False
        self.won = False
        self.message = ""
        self.min_range = 1
        self.max_range = 100
        self.score = 0
        self.hints_used = 0
        self.difficulty = 'medium'
        self.guess_history = []

    def start_new_game(self, difficulty='medium'):
        cfg = DIFFICULTIES.get(difficulty, DIFFICULTIES['medium'])
        self.difficulty = difficulty if difficulty in DIFFICULTIES else 'medium'
        self.min_range = cfg['min']
        self.max_range = cfg['max']
        self.max_attempts = cfg['attempts']
        self.secret_number = random.randint(self.min_range, self.max_range)
        self.attempts = 0
        self.game_over = False
        self.won = False
        self.score = 100
        self.hints_used = 0
        self.guess_history = []
        self.message = f"Pick a number between {self.min_range} and {self.max_range}. You've got {self.max_attempts} tries!"
        return self.message

    def get_hint(self):
        if self.game_over:
            return "The round's over — start a new game for another hint!"
        if self.hints_used >= 2:
            return "You've already used both hints — trust your gut now!"

        self.hints_used += 1
        self.score = max(0, self.score - 10)

        if self.hints_used == 1:
            parity = "even" if self.secret_number % 2 == 0 else "odd"
            hint = f"Hint 1/2: the number is {parity}."
        else:
            digit_sum = sum(int(d) for d in str(self.secret_number))
            hint = f"Hint 2/2: its digits add up to {digit_sum}."
        return hint

    def _temperature(self, guess_num):
        span = max(1, self.max_range - self.min_range)
        distance = abs(guess_num - self.secret_number)
        ratio = distance / span
        if ratio <= 0.02:
            return "🔥 Blazing hot"
        if ratio <= 0.06:
            return "🌶️ Very hot"
        if ratio <= 0.15:
            return "☀️ Warm"
        if ratio <= 0.30:
            return "🌤️ Cool"
        if ratio <= 0.50:
            return "❄️ Cold"
        return "🧊 Freezing"

    def make_guess(self, guess):
        if self.game_over:
            return {"ok": False, "message": "Game's over — start a new one!"}, self.score

        if self.attempts >= self.max_attempts:
            self.game_over = True
            return {"ok": False, "message": f"Out of tries! The number was {self.secret_number}."}, self.score

        try:
            guess_num = int(str(guess).strip())
        except (ValueError, TypeError):
            return {"ok": False, "message": f"That's not a whole number between {self.min_range} and {self.max_range}."}, self.score

        if guess_num < self.min_range or guess_num > self.max_range:
            return {"ok": False, "message": f"Stay within {self.min_range}-{self.max_range}!"}, self.score

        self.attempts += 1
        remaining = self.max_attempts - self.attempts

        if guess_num == self.secret_number:
            self.game_over = True
            self.won = True
            bonus = (self.max_attempts - self.attempts + 1) * 10
            self.score += bonus
            self.guess_history.append({"value": guess_num, "result": "correct"})
            return {
                "ok": True, "won": True,
                "message": f"You nailed it — {self.secret_number} in {self.attempts} tries!",
            }, self.score

        direction = "low" if guess_num < self.secret_number else "high"
        temp = self._temperature(guess_num)
        self.guess_history.append({"value": guess_num, "result": direction})

        if remaining <= 0:
            self.game_over = True
            return {
                "ok": True, "won": False,
                "message": f"So close! Out of tries — the number was {self.secret_number}.",
            }, self.score

        arrow = "📈 Too low" if direction == "low" else "📉 Too high"
        return {
            "ok": True, "won": False,
            "message": f"{arrow} — {temp}. {remaining} {'try' if remaining == 1 else 'tries'} left.",
            "temperature": temp, "direction": direction,
        }, self.score

    def get_game_state(self):
        return {
            'type': 'number',
            'game_over': self.game_over,
            'won': self.won,
            'attempts': self.attempts,
            'max_attempts': self.max_attempts,
            'message': self.message,
            'min_range': self.min_range,
            'max_range': self.max_range,
            'score': self.score,
            'hints_used': self.hints_used,
            'difficulty': self.difficulty,
            'guess_history': self.guess_history,
        }


# ----------------------------------------------------------------------------
# GAME 2: BOLLYWOOD BLOCKBUSTER  (pan-India movies everyone will recognise)
# ----------------------------------------------------------------------------

class MovieGame:
    def __init__(self):
        # Iconic, widely-known pan-India blockbusters spanning decades & languages
        self.words_db = {
            'sholay': 'Amitabh Bachchan & Dharmendra face off against dacoit Gabbar Singh',
            'dilwale dulhania le jayenge': 'Shah Rukh Khan & Kajol — the eternal train-and-mustard-fields romance',
            'lagaan': 'Aamir Khan leads villagers in a cricket match against the British',
            '3 idiots': 'Aamir Khan, R. Madhavan & Sharman Joshi — "All Izz Well"',
            'pk': 'Aamir Khan plays a curious alien questioning religion on Earth',
            'dangal': 'Aamir Khan trains his daughters to become wrestling champions',
            'taare zameen par': 'Aamir Khan helps a dyslexic child discover his talent for art',
            'chak de india': 'Shah Rukh Khan coaches the Indian women\'s hockey team',
            'zindagi na milegi dobara': 'Three friends road-trip through Spain to rediscover life',
            'dil chahta hai': 'Aamir Khan, Saif Ali Khan & Akshaye Khanna — a classic friendship tale',
            'kabhi khushi kabhie gham': 'Shah Rukh Khan, Kajol & Amitabh Bachchan — a big joint-family saga',
            'kuch kuch hota hai': 'Shah Rukh Khan, Kajol & Rani Mukerji — a college love triangle',
            'kal ho naa ho': 'Shah Rukh Khan, Saif Ali Khan & Preity Zinta — set in New York',
            'om shanti om': 'Shah Rukh Khan & Deepika Padukone — reincarnation meets old Bollywood',
            'rang de basanti': 'Aamir Khan and friends turn from carefree youth to revolutionaries',
            'swades': 'Shah Rukh Khan plays a NASA scientist who returns to his Indian village',
            'gully boy': 'Ranveer Singh plays a Mumbai street rapper chasing his dream',
            'andaz apna apna': 'Aamir Khan & Salman Khan in a cult-classic slapstick comedy',
            'hera pheri': 'Akshay Kumar, Sunil Shetty & Paresh Rawal in this iconic comedy caper',
            'golmaal': 'Ajay Devgn leads this hit slapstick comedy franchise',
            'bajrangi bhaijaan': 'Salman Khan helps a mute Pakistani girl find her way home',
            'sultan': 'Salman Khan plays a wrestler making a comeback for love',
            'dabangg': 'Salman Khan plays the swaggering cop Chulbul Pandey',
            'padmaavat': 'Deepika Padukone & Ranveer Singh in Sanjay Leela Bhansali\'s period epic',
            'bajirao mastani': 'Ranveer Singh & Deepika Padukone in a grand Maratha-era love story',
            'devdas': 'Shah Rukh Khan, Aishwarya Rai & Madhuri Dixit in this tragic classic',
            'veer zaara': 'Shah Rukh Khan & Preity Zinta — a cross-border love story',
            'jab we met': 'Shahid Kapoor & Kareena Kapoor — a chatty train encounter changes two lives',
            'yeh jawaani hai deewani': 'Ranbir Kapoor & Deepika Padukone — wanderlust and reunions',
            'barfi': 'Ranbir Kapoor plays a deaf-mute man in this heartwarming tale',
            'queen': 'Kangana Ranaut goes solo on her honeymoon after a called-off wedding',
            'pink': 'Amitabh Bachchan fights a landmark case on consent in court',
            'uri the surgical strike': 'Vicky Kaushal leads a covert army strike — "How\'s the josh?"',
            'mission mangal': 'Akshay Kumar & Vidya Balan dramatize India\'s Mars orbiter mission',
            'baahubali the beginning': 'Prabhas discovers his royal destiny in this epic saga',
            'baahubali 2 the conclusion': 'Prabhas returns — the film that answered "Why Kattappa killed Baahubali"',
            'rrr': 'Jr NTR & Ram Charan in S.S. Rajamouli\'s fiery freedom-fighter epic',
            'kgf chapter 1': 'Yash rises from the slums to rule the Kolar Gold Fields',
            'kgf chapter 2': 'Yash returns as Rocky, taking on a nation-shaking empire',
            'pushpa the rise': 'Allu Arjun plays a fiery red-sandalwood smuggler',
            'pathaan': 'Shah Rukh Khan returns as a spy in this high-octane actioner',
            'jawan': 'Shah Rukh Khan plays a vigilante fighting for the common man',
            'animal': 'Ranbir Kapoor in Sandeep Reddy Vanga\'s intense father-son saga',
            'gadar ek prem katha': 'Sunny Deol crosses the border for love in this partition-era blockbuster',
            'munna bhai mbbs': 'Sanjay Dutt plays a gangster who charms his way into medical college',
            'lage raho munna bhai': 'Sanjay Dutt returns, spreading "Gandhigiri" across Mumbai',
            'drishyam': 'Ajay Devgn goes to extreme lengths to protect his family',
            'stree': 'Rajkummar Rao & Shraddha Kapoor in a horror-comedy about a mysterious spirit',
            'tumbbad': 'A visually stunning horror tale about greed and a forbidden god',
            'shershaah': 'Sidharth Malhotra plays Kargil war hero Captain Vikram Batra',
            'sanju': 'Ranbir Kapoor plays the turbulent life of actor Sanjay Dutt',
            '12th fail': 'Vikrant Massey plays an IPS aspirant who overcomes huge odds',
            'padman': 'Akshay Kumar plays a man revolutionizing menstrual hygiene in rural India',
            'zanjeer': 'Amitabh Bachchan\'s breakout as Bollywood\'s original "Angry Young Man"',
            'sholay ki yaadein': None,  # placeholder removed below
        }
        # remove placeholder if present
        self.words_db.pop('sholay ki yaadein', None)

        self.current_word = None
        self.current_hint = None
        self.scrambled_word = None
        self.attempts = 0
        self.max_attempts = 8
        self.game_over = False
        self.won = False
        self.message = ""
        self.score = 100
        self.hints_used = 0

    def start_new_game(self):
        self.current_word, self.current_hint = random.choice(list(self.words_db.items()))
        self.scrambled_word = self.scramble_word(self.current_word)
        self.attempts = 0
        self.game_over = False
        self.won = False
        self.score = 100
        self.hints_used = 0
        self.message = f"Unscramble the movie title: {self.scrambled_word}"
        return self.message

    def scramble_word(self, word):
        if ' ' in word:
            parts = word.split(' ')
            scrambled_parts = []
            for part in parts:
                word_list = list(part)
                scrambled = word_list[:]
                tries = 0
                while scrambled == word_list and len(part) > 1 and tries < 20:
                    random.shuffle(scrambled)
                    tries += 1
                scrambled_parts.append(''.join(scrambled))
            return ' '.join(scrambled_parts)
        else:
            word_list = list(word)
            scrambled = word_list[:]
            tries = 0
            while scrambled == word_list and len(word) > 1 and tries < 20:
                random.shuffle(scrambled)
                tries += 1
            return ''.join(scrambled)

    def get_hint(self):
        if self.game_over:
            return "The round's over — start a new game for another hint!"
        if self.hints_used >= 2:
            return "You've already used both hints — you've got this!"

        self.hints_used += 1
        self.score = max(0, self.score - 10)

        if self.hints_used == 1:
            hint = f"Hint 1/2: starts with '{self.current_word[0].upper()}', {len(self.current_word)} characters including spaces."
        else:
            hint = f"Hint 2/2: {self.current_hint}"
        return hint

    def make_guess(self, guess):
        if self.game_over:
            return {"ok": False, "message": "Game's over — start a new one!"}, self.score

        if self.attempts >= self.max_attempts:
            self.game_over = True
            return {"ok": False, "message": f"Out of tries! It was '{self.current_word.title()}'."}, self.score

        self.attempts += 1
        remaining = self.max_attempts - self.attempts

        if guess.lower().strip() == self.current_word.lower():
            self.game_over = True
            self.won = True
            bonus = (self.max_attempts - self.attempts + 1) * 20
            self.score += bonus
            return {
                "ok": True, "won": True,
                "message": f"Correct — it's '{self.current_word.title()}'! You know your cinema!",
            }, self.score

        if remaining <= 0:
            self.game_over = True
            return {
                "ok": True, "won": False,
                "message": f"Out of tries! It was '{self.current_word.title()}'.",
            }, self.score

        return {
            "ok": True, "won": False,
            "message": f"Not quite — {remaining} {'try' if remaining == 1 else 'tries'} left.",
        }, self.score

    def get_game_state(self):
        return {
            'type': 'word',
            'game_over': self.game_over,
            'won': self.won,
            'attempts': self.attempts,
            'max_attempts': self.max_attempts,
            'message': self.message,
            'scrambled_word': self.scrambled_word,
            'hint': self.current_hint,
            'score': self.score,
            'hints_used': self.hints_used,
            'word_length': len(self.current_word) if self.current_word else 0,
        }


# ----------------------------------------------------------------------------
# GAME 3: PICTURE ROUND  (guess-from-the-picture — big visual emoji clues,
# no external images needed so it loads instantly on a shared screen)
# ----------------------------------------------------------------------------

class PictureGame:
    """GAME 3: WORD RUSH — 30 tough jumbles + 30 hard missing-letter puzzles."""

    JUMBLES = [
        ('scramble','ATZNIMTPOOII',['optimization'],'Improving something so it performs better.'),
        ('scramble','RTACRTCEHIEU',['architecture'],'The design/structure of a system.'),
        ('scramble','TIAIENRNGOT',['integration'],'Connecting systems or components together.'),
        ('scramble','TTOMUINAOA',['automation'],'Reducing repetitive manual work.'),
        ('scramble','TCIGUNIOOFNAR',['configuration'],'System settings and parameters.'),
        ('scramble','LMEYTENODP',['deployment'],'Putting an application into an environment.'),
        ('scramble','IHBROUOLONESTGT',['troubleshooting'],'Finding and fixing the cause of an issue.'),
        ('scramble','BIYSLTAIACL',['scalability'],'Ability to handle increasing load.'),
        ('scramble','AIILYTRBLEI',['reliability'],'Consistent correct operation.'),
        ('scramble','ORANTNNIZAIOTICE',['containerization'],'Packaging an application with its dependencies.'),
        ('scramble','ANTOCCIUNIMOM',['communication'],'Sharing information clearly with others.'),
        ('scramble','LAROONITBACLO',['collaboration'],'Working together toward a goal.'),
        ('scramble','SIINETRIYPOLBS',['responsibility'],'Being accountable for something.'),
        ('scramble','CEIYIFFCNE',['efficiency'],'Doing useful work with minimal waste.'),
        ('scramble','EKNROWNTGI',['networking'],'Building professional connections.'),
        ('scramble','ETRNSKEBEU',['kubernetes'],'Container orchestration platform.'),
        ('scramble','THMUPEEROS',['prometheus'],'Monitoring and alerting platform.'),
        ('scramble','SEVRCIRSCIMEO',['microservices'],'Architecture made from small independent services.'),
        ('scramble','OABIAANNGCDLL',['loadbalancing'],'Distributing traffic across servers.'),
        ('scramble','RAPCVENSREEE',['perseverance'],'Continuing despite difficulty.'),
        ('scramble','NDANTIMITOERE',['determination'],'Staying committed despite obstacles.'),
        ('scramble','BIYTDAILAPAT',['adaptability'],'Ability to adjust to change.'),
        ('scramble','ILBYUCCTATOINA',['accountability'],'Taking ownership of results.'),
        ('scramble','ITUDPCIVRTYO',['productivity'],'Amount of useful work achieved.'),
        ('scramble','NOAOVTNNII',['innovation'],'Introducing a new idea or method.'),
        ('scramble','OAICNNCTETORN',['concentration'],'Focused attention.'),
        ('scramble','AIOAITNMIGN',['imagination'],'Ability to form ideas mentally.'),
        ('scramble','IOHIMCAPHNSP',['championship'],'Competition to decide the best.'),
        ('scramble','ENCOTMPIITO',['competition'],'A contest between people or teams.'),
        ('scramble','TNRLAEBIECO',['celebration'],'A happy event marking something special.')
    ]

    MISSING = [
        ('missing','O_TI_I___I_N',['optimization'],'Improving something so it performs better.'),
        ('missing','AR__I__C_URE',['architecture'],'The design/structure of a system.'),
        ('missing','I_T_GRA_I_N',['integration'],'Connecting systems or components together.'),
        ('missing','A_T_M___ON',['automation'],'Reducing repetitive manual work.'),
        ('missing','C___I_UR__ION',['configuration'],'System settings and parameters.'),
        ('missing','D_P__Y_ENT',['deployment'],'Putting an application into an environment.'),
        ('missing','TRO__LES____I_G',['troubleshooting'],'Finding and fixing the cause of an issue.'),
        ('missing','SC_L_B__I_Y',['scalability'],'Ability to handle increasing load.'),
        ('missing','R_L___IL_TY',['reliability'],'Consistent correct operation.'),
        ('missing','C_NT__NE_IZ_TI_N',['containerization'],'Packaging an application with its dependencies.'),
        ('missing','COMM_NI____ON',['communication'],'Sharing information clearly with others.'),
        ('missing','C___AB_RATION',['collaboration'],'Working together toward a goal.'),
        ('missing','R____N_I_ILITY',['responsibility'],'Being accountable for something.'),
        ('missing','E__ICI_N_Y',['efficiency'],'Doing useful work with minimal waste.'),
        ('missing','NE__ORKI_G',['networking'],'Building professional connections.'),
        ('missing','KUB_R___ES',['kubernetes'],'Container orchestration platform.'),
        ('missing','P__ME_HE_S',['prometheus'],'Monitoring and alerting platform.'),
        ('missing','M_CROS__VIC_S',['microservices'],'Architecture made from small independent services.'),
        ('missing','L___B_LANC__G',['loadbalancing'],'Distributing traffic across servers.'),
        ('missing','P_RS__ER_N_E',['perseverance'],'Continuing despite difficulty.'),
        ('missing','DET_RMINA___N',['determination'],'Staying committed despite obstacles.'),
        ('missing','AD_PTA_I_I_Y',['adaptability'],'Ability to adjust to change.'),
        ('missing','A_CO_N_A___ITY',['accountability'],'Taking ownership of results.'),
        ('missing','PR___CT_VI_Y',['productivity'],'Amount of useful work achieved.'),
        ('missing','I_N_V___ON',['innovation'],'Introducing a new idea or method.'),
        ('missing','C__C_N_R_TI_N',['concentration'],'Focused attention.'),
        ('missing','I___IN_TION',['imagination'],'Ability to form ideas mentally.'),
        ('missing','CHA__I_NS__P',['championship'],'Competition to decide the best.'),
        ('missing','C___ETI__ON',['competition'],'A contest between people or teams.'),
        ('missing','C___BRATI_N',['celebration'],'A happy event marking something special.')
    ]

    CATEGORIES = {
        'mixed': {'label':'🎲 Mixed Challenge','items': JUMBLES + MISSING},
        'scramble': {'label':'🔀 Hard Jumble','items': JUMBLES},
        'missing': {'label':'🕵️ Hard Missing Letters','items': MISSING},
        'fun': {'label':'🎉 Friday Fun — Hard','items': JUMBLES + MISSING},
    }

    def __init__(self):
        self.game_over = False
        self.won = False
        self.attempts = 0
        self.max_attempts = 7
        self.score = 100
        self.hints_used = 0
        self.current_clue = ''
        self.current_answers = []
        self.current_hint = ''
        self.current_mode = 'scramble'
        self.category = 'mixed'
        self.category_label = '🎲 Mixed Challenge'
        self.message = ''

    def start_new_game(self, category='mixed'):
        if category not in self.CATEGORIES:
            category = 'mixed'
        self.category = category
        mode, clue, answers, hint = random.choice(self.CATEGORIES[category]['items'])
        self.current_mode = mode
        self.current_clue = clue.upper()
        self.current_answers = answers
        self.current_hint = hint
        self.category_label = self.CATEGORIES[category]['label']
        self.game_over = False
        self.won = False
        self.attempts = 0
        self.max_attempts = 7
        self.score = 100
        self.hints_used = 0
        self.message = '🔀 Unscramble ALL the letters!' if mode == 'scramble' else '🕵️ Fill in ALL the missing letters!'
        return self.get_game_state()

    @staticmethod
    def normalize(value):
        return re.sub(r'[^a-z0-9]+', '', str(value).lower())

    def make_guess(self, guess):
        if self.game_over:
            return {'ok':False,'won':self.won,'message':'This round is over — click Next Word!'}, self.score
        guess_norm = self.normalize(guess)
        if not guess_norm:
            return {'ok':False,'won':False,'message':'Type your answer first!'}, self.score
        self.attempts += 1
        accepted = {self.normalize(a) for a in self.current_answers}
        if guess_norm in accepted:
            self.won = True
            self.game_over = True
            bonus = max(10, (self.max_attempts - self.attempts + 1) * 15)
            self.score += bonus
            return {'ok':True,'won':True,'message':f"🎉 CORRECT! {self.current_answers[0].upper()} • +{bonus} bonus!"}, self.score
        remaining = self.max_attempts - self.attempts
        if remaining <= 0:
            self.game_over = True
            return {'ok':True,'won':False,'message':f"😅 Out of tries! The answer was {self.current_answers[0].upper()}."}, self.score
        self.score = max(0, self.score - 8)
        return {'ok':True,'won':False,'message':f"❌ Not quite. {remaining} tries left."}, self.score

    def get_hint(self):
        if self.game_over:
            return 'The round is over — click Next Word!'
        if self.hints_used >= 2:
            return '🚫 No hints left for this round.'
        self.hints_used += 1
        self.score = max(0, self.score - 10)
        answer = self.current_answers[0]
        if self.hints_used == 1:
            return f"💡 Hint: {len(answer)} letters • starts with '{answer[0].upper()}'."
        return f'💡 Hint: {self.current_hint}'

    def get_game_state(self):
        return {
            'type':'picture','game_over':self.game_over,'won':self.won,
            'attempts':self.attempts,'max_attempts':self.max_attempts,
            'message':self.message,'clue':self.current_clue,
            'category_label':self.category_label,'category':self.category,
            'mode':self.current_mode,'score':self.score,'hints_used':self.hints_used,
        }


class GameFour:
    """GAME 4: FIND THE INTRUDER — 30 quick pattern-recognition questions."""

    QUESTIONS = [
        (['Docker','Kubernetes','Jenkins','Mango'],3,'Three are DevOps tools/platforms; one is a fruit.'),
        (['Git','GitHub','GitLab','Python'],3,'Three are directly related to Git/repository workflows; one is a programming language.'),
        (['CPU','RAM','SSD','Ubuntu'],3,'Three are hardware components; one is an operating system.'),
        (['AWS','Azure','GCP','Jenkins'],3,'Three are cloud providers; one is a CI/CD tool.'),
        (['Deployment','Pipeline','Monitoring','Banana'],3,'Three are DevOps concepts; one is food.'),
        (['Pod','Service','Ingress','Keyboard'],3,'Three are Kubernetes concepts; one is hardware.'),
        (['Linux','Windows','Ubuntu','Nginx'],3,'Three are operating systems/distributions; one is a web server.'),
        (['Terraform','Ansible','Pulumi','Grafana'],3,'Three are infrastructure/automation tools; one is primarily observability.'),
        (['Jenkins','GitHub Actions','GitLab CI','Photoshop'],3,'Three can run CI/CD workflows; one is an image editor.'),
        (['TCP','UDP','HTTP','JPEG'],3,'Three are networking/protocol concepts; one is an image format.'),
        (['S3','EC2','Lambda','Excel'],3,'Three are AWS services; one is a spreadsheet application.'),
        (['Dockerfile','Jenkinsfile','pom.xml','Birthday'],3,'Three are common software/project files; one is not.'),
        (['Scale','Deploy','Monitor','Sandwich'],3,'Three are engineering actions/concepts; one is food.'),
        (['Load Balancer','Reverse Proxy','API Gateway','Guitar'],3,'Three can sit in front of services/traffic; one is an instrument.'),
        (['Blue-Green','Canary','Rolling','Chocolate'],3,'Three are deployment strategies; one is food.'),
        (['Helm','kubectl','kubelet','Spotify'],3,'Three are Kubernetes-related; one is a music service.'),
        (['Prometheus','Grafana','Alertmanager','Calculator'],3,'Three are observability-related; one is a general utility.'),
        (['Branch','Commit','Merge','Microwave'],3,'Three are Git concepts; one is an appliance.'),
        (['Bug','Incident','Outage','Birthday'],3,'Three can be production/support events; one is a celebration.'),
        (['Latency','Throughput','Availability','Watermelon'],3,'Three are system/performance concepts; one is fruit.'),
        (['Hash','Encryption','Certificate','Pizza'],3,'Three relate to security/cryptography; one is food.'),
        (['SSH','RDP','FTP','Instagram'],3,'Three are technical protocols/access methods; one is social media.'),
        (['JSON','YAML','XML','Burger'],3,'Three are data/configuration formats; one is food.'),
        (['Nginx','Apache','IIS','Jira'],3,'Three are web servers; one is project-management software.'),
        (['Maven','Gradle','npm','Kubernetes'],3,'Three are build/package tools; one is orchestration.'),
        (['Dev','Test','Prod','Dessert'],3,'Three are common environment names; one is food.'),
        (['Node','Pod','Container','Notebook'],3,'Three are infrastructure/container terms; one is stationery.'),
        (['Scale Up','Scale Out','Autoscaling','Photocopy'],3,'Three relate to scaling systems; one does not.'),
        (['Logs','Metrics','Traces','Luggage'],3,'Three are observability signals; one is travel-related.'),
        (['README','LICENSE','Dockerfile','Waterfall'],3,'Three are commonly found in software repositories; one is a development model.'),
    ]

    def __init__(self):
        self.index = 0
        self.score = 0
        self.questions = random.sample(self.QUESTIONS, len(self.QUESTIONS))

    def new_round(self):
        if self.index >= len(self.questions):
            self.questions = random.sample(self.QUESTIONS, len(self.QUESTIONS))
            self.index = 0
        q = self.questions[self.index]
        return {'game':4,'question_no':self.index+1,'total':len(self.questions),'options':q[0],'hint':q[2]}

    def answer(self, choice):
        q = self.questions[self.index]
        correct = q[1]
        ok = int(choice) == correct
        if ok:
            self.score += 100
        self.index += 1
        return {'ok':ok,'correct':correct,'score':self.score,'message':'🎯 Correct!' if ok else f"❌ Correct answer: {q[0][correct]}"}


# ----------------------------------------------------------------------------
# SESSION / STATE MANAGEMENT
# ----------------------------------------------------------------------------

games = {}
leaderboard_scores = []


def get_session(session_id):
    if session_id not in games:
        games[session_id] = {'active_game': None, 'game_type': None}
    return games[session_id]


# ----------------------------------------------------------------------------
# ROUTES
# ----------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template_string(PAGE_TEMPLATE)


@app.route('/select_game', methods=['POST'])
def select_game():
    session_id = request.headers.get('X-Session-ID', 'default')
    data = request.get_json(force=True, silent=True) or {}
    game_type = data.get('game_type')
    difficulty = data.get('difficulty', 'medium')
    category = data.get('category', 'mixed')

    session_data = get_session(session_id)

    if game_type == 'number':
        session_data['active_game'] = NumberGame()
        session_data['game_type'] = 'number'
        session_data['active_game'].start_new_game(difficulty)
    elif game_type == 'word':
        session_data['active_game'] = MovieGame()
        session_data['game_type'] = 'word'
        session_data['active_game'].start_new_game()
    elif game_type == 'picture':
        session_data['active_game'] = PictureGame()
        session_data['game_type'] = 'picture'
        session_data['active_game'].start_new_game(category)
    else:
        return jsonify({'error': 'Invalid game type'}), 400

    return jsonify(session_data['active_game'].get_game_state())


@app.route('/new_game', methods=['POST'])
def new_game():
    session_id = request.headers.get('X-Session-ID', 'default')
    data = request.get_json(force=True, silent=True) or {}
    difficulty = data.get('difficulty', 'medium')
    category = data.get('category', 'mixed')
    session_data = get_session(session_id)

    if not session_data['active_game']:
        return jsonify({'error': 'No game selected'}), 400

    if session_data['game_type'] == 'number':
        session_data['active_game'].start_new_game(difficulty)
    elif session_data['game_type'] == 'picture':
        session_data['active_game'].start_new_game(category)
    else:
        session_data['active_game'].start_new_game()

    return jsonify(session_data['active_game'].get_game_state())


@app.route('/guess', methods=['POST'])
def guess():
    session_id = request.headers.get('X-Session-ID', 'default')
    session_data = get_session(session_id)

    if not session_data['active_game']:
        return jsonify({'error': 'No game selected'}), 400

    data = request.get_json(force=True, silent=True) or {}
    guess_value = data.get('guess', '')

    result, score = session_data['active_game'].make_guess(guess_value)

    return jsonify({
        'result': result,
        'game_state': session_data['active_game'].get_game_state()
    })


@app.route('/hint', methods=['POST'])
def hint():
    session_id = request.headers.get('X-Session-ID', 'default')
    session_data = get_session(session_id)

    if not session_data['active_game']:
        return jsonify({'error': 'No game selected'}), 400

    hint_message = session_data['active_game'].get_hint()

    return jsonify({
        'message': hint_message,
        'game_state': session_data['active_game'].get_game_state()
    })


@app.route('/game_state', methods=['GET'])
def game_state():
    session_id = request.headers.get('X-Session-ID', 'default')
    session_data = get_session(session_id)

    if not session_data['active_game']:
        return jsonify({'error': 'No game selected', 'game_selected': False})

    return jsonify(session_data['active_game'].get_game_state())


@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    sorted_scores = sorted(leaderboard_scores, key=lambda x: x['score'], reverse=True)[:10]
    return jsonify(sorted_scores)


@app.route('/save_score', methods=['POST'])
def save_score():
    session_id = request.headers.get('X-Session-ID', 'default')
    data = request.get_json(force=True, silent=True) or {}
    player_name = (data.get('player_name') or 'Anonymous').strip()[:20]
    session_data = get_session(session_id)

    if not session_data['active_game']:
        return jsonify({'error': 'No game selected'}), 400

    state = session_data['active_game'].get_game_state()
    if state['game_over']:
        leaderboard_scores.append({
            'player_name': player_name or 'Anonymous',
            'score': state['score'],
            'game_type': state['type'],
            'won': state.get('won', False),
            'attempts_used': state['attempts'],
            'date': datetime.now().strftime('%d %b, %I:%M %p'),
        })
        del leaderboard_scores[:-100]
        return jsonify({'success': True, 'message': 'Score saved!'})

    return jsonify({'success': False, 'message': 'Finish the round first!'})


# ----------------------------------------------------------------------------
# FRONT-END (single-file template — HTML + CSS + JS)
# ----------------------------------------------------------------------------

PAGE_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Friday Fun Night 🎬🍿</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root{
    --curtain-1:#3c0a14;
    --curtain-2:#7a1225;
    --gold:#e8c468;
    --gold-soft:#f3dfa2;
    --cream:#f7ecd8;
    --ink:#1b1210;
    --panel:#241417;
    --panel-2:#2e181b;
    --good:#59c48a;
    --bad:#e2665a;
    --shadow: 0 20px 60px rgba(0,0,0,.45);
  }
  *{box-sizing:border-box;}
  html,body{height:100%;}
  body{
    margin:0;
    font-family:'Poppins',sans-serif;
    color:var(--cream);
    background:
      radial-gradient(1200px 600px at 50% -10%, #4a0f1e 0%, transparent 60%),
      linear-gradient(180deg, var(--curtain-1) 0%, #1a0509 55%, #10070a 100%);
    min-height:100vh;
    overflow-x:hidden;
    position:relative;
  }
  /* velvet curtain folds */
  body::before{
    content:"";
    position:fixed; inset:0;
    background:repeating-linear-gradient(
      90deg,
      rgba(255,255,255,0.03) 0px,
      rgba(0,0,0,0.10) 40px,
      rgba(255,255,255,0.03) 80px
    );
    pointer-events:none;
    z-index:0;
  }
  .stage{
    position:relative; z-index:1;
    max-width:960px;
    margin:0 auto;
    padding:36px 20px 80px;
  }

  /* ---------- Marquee header ---------- */
  .marquee{
    position:relative;
    text-align:center;
    padding:26px 20px 30px;
    margin-bottom:34px;
    border-radius:18px;
    background:linear-gradient(180deg, var(--panel) 0%, var(--panel-2) 100%);
    box-shadow:var(--shadow), inset 0 0 0 1px rgba(232,196,104,0.25);
  }
  .marquee .bulbs{
    position:absolute; inset:8px;
    border-radius:12px;
    pointer-events:none;
  }
  .marquee .bulbs span{
    position:absolute;
    width:7px;height:7px;border-radius:50%;
    background:var(--gold);
    box-shadow:0 0 8px 2px rgba(232,196,104,.9);
    animation:twinkle 1.6s infinite ease-in-out;
  }
  @keyframes twinkle{
    0%,100%{opacity:.25; transform:scale(.85);}
    50%{opacity:1; transform:scale(1.15);}
  }
  .marquee .eyebrow{
    letter-spacing:.35em;
    font-size:11px;
    color:var(--gold-soft);
    text-transform:uppercase;
    margin-bottom:8px;
    opacity:.85;
  }
  .marquee h1{
    font-family:'Playfair Display',serif;
    font-weight:900;
    font-size:clamp(28px, 5vw, 46px);
    margin:0;
    background:linear-gradient(180deg, var(--gold-soft), var(--gold) 60%, #b98a2f);
    -webkit-background-clip:text;
    background-clip:text;
    color:transparent;
    text-shadow:0 2px 0 rgba(0,0,0,.2);
  }
  .marquee p.tagline{
    margin:10px 0 0;
    color:var(--cream);
    opacity:.75;
    font-size:14px;
  }

  /* ---------- Game picker ---------- */
  .picker{
    display:grid;
    grid-template-columns:1fr 1fr 1fr;
    gap:18px;
    margin-bottom:26px;
  }
  @media (max-width:820px){ .picker{grid-template-columns:1fr 1fr;} }
  @media (max-width:520px){ .picker{grid-template-columns:1fr;} }

  .game-card{
    cursor:pointer;
    text-align:left;
    border:1px solid rgba(232,196,104,0.22);
    background:linear-gradient(160deg, var(--panel) 0%, var(--panel-2) 100%);
    border-radius:16px;
    padding:22px;
    position:relative;
    overflow:hidden;
    transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease;
  }
  .game-card:hover{
    transform:translateY(-4px);
    box-shadow:var(--shadow);
    border-color:var(--gold);
  }
  .game-card .icon{font-size:34px;}
  .game-card h3{
    font-family:'Playfair Display',serif;
    margin:10px 0 6px;
    font-size:22px;
    color:var(--gold-soft);
  }
  .game-card p{margin:0; font-size:13.5px; opacity:.75; line-height:1.5;}
  .game-card .spark{
    position:absolute; right:-30px; top:-30px;
    width:110px; height:110px;
    background:radial-gradient(circle, rgba(232,196,104,.25), transparent 70%);
  }

  /* ---------- Panels ---------- */
  .panel{
    background:linear-gradient(160deg, var(--panel) 0%, var(--panel-2) 100%);
    border:1px solid rgba(232,196,104,0.2);
    border-radius:18px;
    padding:28px;
    box-shadow:var(--shadow);
    display:none;
  }
  .panel.active{display:block;}

  .panel-top{
    display:flex; justify-content:space-between; align-items:center;
    flex-wrap:wrap; gap:10px;
    margin-bottom:18px;
    padding-bottom:14px;
    border-bottom:1px dashed rgba(232,196,104,0.25);
  }
  .panel-top .title{
    font-family:'Playfair Display',serif;
    font-size:20px;
    color:var(--gold-soft);
  }
  .stat-row{display:flex; gap:14px; flex-wrap:wrap;}
  .stat{
    background:rgba(0,0,0,.25);
    border:1px solid rgba(232,196,104,.18);
    border-radius:10px;
    padding:6px 12px;
    font-size:12.5px;
    display:flex; align-items:center; gap:6px;
  }
  .stat b{color:var(--gold-soft); font-size:14px;}

  .diff-row{display:flex; gap:8px; margin-bottom:16px; flex-wrap:wrap;}
  .diff-btn{
    padding:7px 14px; border-radius:999px; cursor:pointer;
    border:1px solid rgba(232,196,104,.3);
    background:transparent; color:var(--cream); font-size:12.5px;
    transition:all .15s ease;
  }
  .diff-btn.active, .diff-btn:hover{
    background:var(--gold); color:#241417; font-weight:600; border-color:var(--gold);
  }

  .difficulty-badge{
    width:max-content;
    margin:0 auto 12px;
    padding:4px 10px;
    border:1px solid rgba(232,196,104,.35);
    border-radius:999px;
    font-size:10px;
    font-weight:700;
    letter-spacing:.15em;
    color:var(--gold-soft);
    opacity:.75;
  }

  .word-mode{
    text-align:center;
    margin:10px 0 8px;
    font-size:12px;
    letter-spacing:.2em;
    font-weight:700;
    color:var(--gold-soft);
    opacity:.85;
  }
  .word-clue{
    font-family:'Poppins',sans-serif;
    font-weight:800;
    letter-spacing:10px !important;
    word-break:break-word;
  }

  .rebus-intro{
    text-align:center;
    margin:8px 0 10px;
    font-size:12px;
    letter-spacing:.22em;
    font-weight:700;
    color:var(--gold-soft);
    opacity:.8;
  }
  .rebus-frame{
    padding:42px 18px 30px;
    min-height:190px;
    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;
  }
  .rebus-frame .clue{
    font-size:clamp(56px, 12vw, 105px);
    letter-spacing:8px;
    line-height:1.25;
  }
  .rebus-tip{
    text-align:center;
    font-size:12px;
    opacity:.6;
    margin:-6px 0 14px;
  }

  .picture-frame{
    text-align:center;
    padding:34px 10px 30px;
    margin:6px 0 18px;
    border-radius:14px;
    background:
      radial-gradient(circle at 50% 30%, rgba(232,196,104,.10), transparent 65%),
      repeating-linear-gradient(45deg, rgba(232,196,104,.05) 0 10px, rgba(0,0,0,.12) 10px 20px);
    border:1px dashed rgba(232,196,104,.35);
  }
  .picture-frame .clue{
    font-size:clamp(48px, 10vw, 84px);
    line-height:1.1;
    letter-spacing:6px;
    filter:drop-shadow(0 6px 14px rgba(0,0,0,.5));
  }
  .picture-frame .cat-tag{
    margin-top:10px;
    font-size:12px;
    letter-spacing:.15em;
    text-transform:uppercase;
    color:var(--gold-soft);
    opacity:.75;
  }

  .scramble-box{
    text-align:center;
    font-size:clamp(22px, 4.4vw, 34px);
    letter-spacing:3px;
    font-family:'Playfair Display',serif;
    color:var(--gold-soft);
    padding:22px 10px;
    margin:6px 0 18px;
    border-radius:14px;
    background:repeating-linear-gradient(45deg, rgba(232,196,104,.05) 0 10px, rgba(0,0,0,.12) 10px 20px);
    border:1px dashed rgba(232,196,104,.35);
    word-break:break-word;
  }

  .range-hint{
    text-align:center;
    font-size:13px;
    opacity:.7;
    margin-bottom:14px;
  }

  .thermo{
    height:10px; border-radius:999px; overflow:hidden;
    background:rgba(0,0,0,.35);
    margin:14px 0 6px;
    display:none;
  }
  .thermo.show{display:block;}
  .thermo-fill{
    height:100%;
    width:0%;
    background:linear-gradient(90deg, #4aa3f0, #59c48a, #f0c93a, #e2665a);
    transition:width .4s ease;
  }

  .msg{
    text-align:center;
    min-height:26px;
    font-size:15px;
    font-weight:500;
    margin:10px 0 18px;
    transition:color .2s ease;
  }
  .msg.good{color:var(--good);}
  .msg.bad{color:var(--bad);}

  .input-row{
    display:flex; gap:10px; flex-wrap:wrap;
  }
  input[type=text], input[type=number]{
    flex:1 1 180px;
    padding:13px 16px;
    border-radius:12px;
    border:1px solid rgba(232,196,104,.35);
    background:rgba(0,0,0,.3);
    color:var(--cream);
    font-size:15px;
    font-family:'Poppins',sans-serif;
    outline:none;
  }
  input:focus{border-color:var(--gold); box-shadow:0 0 0 3px rgba(232,196,104,.15);}

  button{
    font-family:'Poppins',sans-serif;
    cursor:pointer;
    border:none;
    border-radius:12px;
    padding:13px 20px;
    font-size:14px;
    font-weight:600;
    transition:transform .12s ease, opacity .12s ease;
  }
  button:active{transform:scale(.96);}
  button:focus-visible{outline:2px solid var(--gold-soft); outline-offset:2px;}
  .btn-primary{background:linear-gradient(180deg, var(--gold-soft), var(--gold)); color:#241417;}
  .btn-secondary{background:rgba(255,255,255,.08); color:var(--cream); border:1px solid rgba(232,196,104,.3);}
  .btn-ghost{background:transparent; color:var(--gold-soft); border:1px solid rgba(232,196,104,.3);}
  .btn-row{display:flex; gap:10px; margin-top:16px; flex-wrap:wrap;}
  .btn-row button{flex:1 1 auto;}

  .history{
    display:flex; gap:6px; flex-wrap:wrap; margin-top:14px;
  }
  .chip{
    padding:5px 10px; border-radius:8px; font-size:12px;
    background:rgba(0,0,0,.3); border:1px solid rgba(232,196,104,.2);
  }
  .chip.low{color:#7fb8ff;}
  .chip.high{color:#ff9d8a;}
  .chip.correct{color:var(--good); border-color:var(--good);}

  .back-link{
    display:inline-block; margin-bottom:16px; cursor:pointer;
    color:var(--gold-soft); font-size:13px; opacity:.8;
  }
  .back-link:hover{opacity:1;}

  /* ---------- Leaderboard ---------- */
  .leaderboard{
    margin-top:30px;
    background:linear-gradient(160deg, var(--panel) 0%, var(--panel-2) 100%);
    border:1px solid rgba(232,196,104,0.2);
    border-radius:18px;
    padding:22px 24px;
    box-shadow:var(--shadow);
  }
  .leaderboard h3{
    font-family:'Playfair Display',serif;
    color:var(--gold-soft);
    margin:0 0 14px;
    font-size:18px;
  }
  .lb-row{
    display:flex; justify-content:space-between; align-items:center;
    padding:9px 0;
    border-bottom:1px solid rgba(255,255,255,.06);
    font-size:13.5px;
  }
  .lb-row:last-child{border-bottom:none;}
  .lb-rank{width:26px; color:var(--gold-soft); font-weight:700;}
  .lb-name{flex:1; opacity:.9;}
  .lb-score{font-weight:700; color:var(--gold-soft);}
  .lb-empty{opacity:.6; font-size:13px; text-align:center; padding:10px 0;}

  /* ---------- Confetti / win overlay ---------- */
  #confetti-canvas{
    position:fixed; inset:0; pointer-events:none; z-index:50;
  }
  .win-banner{
    position:fixed; left:50%; top:18px; transform:translateX(-50%) translateY(-40px);
    background:linear-gradient(180deg, var(--gold-soft), var(--gold));
    color:#241417; font-weight:700; padding:12px 22px; border-radius:999px;
    box-shadow:0 12px 30px rgba(0,0,0,.4);
    opacity:0; transition:all .35s ease;
    z-index:60; font-size:14px;
  }
  .win-banner.show{opacity:1; transform:translateX(-50%) translateY(0);}

  footer{
    text-align:center; margin-top:40px; font-size:12px; opacity:.4;
  }
</style>
</head>
<body>

<canvas id="confetti-canvas"></canvas>
<div class="win-banner" id="winBanner">🎉 Great guess!</div>

<div class="stage">

  <div class="marquee">
    <div class="bulbs" id="bulbs"></div>
    <div class="eyebrow">Team Friday Fun</div>
    <h1>🎬 The Arcade Screening</h1>
    <p class="tagline">Three games. One screen. Bragging rights on the line.</p>
  </div>

  <div class="picker" id="picker">
    <div class="game-card" onclick="chooseGame('number')">
      <div class="spark"></div>
      <div class="icon">🔢</div>
      <h3>Number Quest</h3>
      <p>Hot-or-cold number hunting with difficulty levels, live temperature clues and streak bonuses.</p>
    </div>
    <div class="game-card" onclick="chooseGame('word')">
      <div class="spark"></div>
      <div class="icon">🎞️</div>
      <h3>Bollywood Blockbuster</h3>
      <p>Unscramble iconic pan-India movies everyone on the call will recognise — from Sholay to RRR.</p>
    </div>
    <div class="game-card" onclick="chooseGame('picture')">
      <div class="spark"></div>
      <div class="icon">🔀</div>
      <h3>Word Rush</h3>
      <p>Unscramble letters, complete missing letters and race the clock to find the hidden word before your teammates do!</p>
    </div>
  </div>

  <!-- NUMBER GAME PANEL -->
  <div class="panel" id="numberPanel">
    <span class="back-link" onclick="backToPicker()">← Back to games</span>
    <div class="panel-top">
      <div class="title">🔢 Number Quest</div>
      <div class="stat-row">
        <div class="stat">Score <b id="numScore">100</b></div>
        <div class="stat">Try <b id="numAttempts">0</b>/<span id="numMaxAttempts">10</span></div>
        <div class="stat">Hints <b id="numHints">0</b>/2</div>
      </div>
    </div>

    <div class="diff-row" id="diffRow">
      <button class="diff-btn" data-diff="easy" onclick="setDifficulty('easy')">Easy (1-50)</button>
      <button class="diff-btn active" data-diff="medium" onclick="setDifficulty('medium')">Medium (1-100)</button>
      <button class="diff-btn" data-diff="hard" onclick="setDifficulty('hard')">Hard (1-300)</button>
    </div>

    <p class="range-hint" id="numRangeHint">Pick a number between 1 and 100</p>

    <div class="thermo" id="thermo"><div class="thermo-fill" id="thermoFill"></div></div>

    <div class="msg" id="numMsg"></div>

    <div class="input-row">
      <input type="number" id="numInput" placeholder="Your guess…" onkeydown="if(event.key==='Enter')submitNumberGuess()">
      <button class="btn-primary" onclick="submitNumberGuess()">Guess</button>
    </div>

    <div class="history" id="numHistory"></div>

    <div class="btn-row">
      <button class="btn-secondary" onclick="getHint('number')">💡 Hint (-10)</button>
      <button class="btn-ghost" onclick="startGame('number')">🔁 New Round</button>
      <button class="btn-primary" id="numSaveBtn" style="display:none" onclick="saveScore()">🏆 Save Score</button>
    </div>
  </div>

  <!-- MOVIE GAME PANEL -->
  <div class="panel" id="wordPanel">
    <span class="back-link" onclick="backToPicker()">← Back to games</span>
    <div class="panel-top">
      <div class="title">🎞️ Bollywood Blockbuster</div>
      <div class="stat-row">
        <div class="stat">Score <b id="wordScore">100</b></div>
        <div class="stat">Try <b id="wordAttempts">0</b>/<span id="wordMaxAttempts">8</span></div>
        <div class="stat">Hints <b id="wordHints">0</b>/2</div>
      </div>
    </div>

    <div class="scramble-box" id="scrambleBox">…</div>

    <div class="msg" id="wordMsg"></div>

    <div class="input-row">
      <input type="text" id="wordInput" placeholder="Type the movie name…" onkeydown="if(event.key==='Enter')submitWordGuess()">
      <button class="btn-primary" onclick="submitWordGuess()">Guess</button>
    </div>

    <div class="btn-row">
      <button class="btn-secondary" onclick="getHint('word')">💡 Hint (-10)</button>
      <button class="btn-ghost" onclick="startGame('word')">🔁 New Movie</button>
      <button class="btn-primary" id="wordSaveBtn" style="display:none" onclick="saveScore()">🏆 Save Score</button>
    </div>
  </div>

  <!-- GAME 3: WORD RUSH -->
  <div class="panel" id="picturePanel">
    <span class="back-link" onclick="backToPicker()">← Back to games</span>
    <div class="panel-top">
      <div class="title">🔀 Word Rush</div>
      <div class="stat-row">
        <div class="stat">Score <b id="picScore">100</b></div>
        <div class="stat">Try <b id="picAttempts">0</b>/<span id="picMaxAttempts">6</span></div>
        <div class="stat">Hints <b id="picHints">0</b>/2</div>
      </div>
    </div>

    <div class="diff-row" id="catRow">
      <button class="diff-btn active" data-cat="mixed" onclick="setCategory('mixed')">🎲 Mixed</button>
      <button class="diff-btn" data-cat="scramble" onclick="setCategory('scramble')">🔀 Hard Jumble</button>
      <button class="diff-btn" data-cat="missing" onclick="setCategory('missing')">🕵️ Hard Missing</button>
      <button class="diff-btn" data-cat="fun" onclick="setCategory('fun')">🎉 Fun Words</button>
    </div>

    <div class="word-mode" id="wordMode">🔀 UNSCRAMBLE THE WORD</div>
    <div class="difficulty-badge">MEDIUM • HARD</div>

    <div class="picture-frame rebus-frame">
      <div class="clue word-clue" id="picClue">_ _ _ _</div>
      <div class="cat-tag" id="picCatTag">🎲 Mixed Challenge</div>
    </div>

    <div class="rebus-tip" id="wordTip">💭 No easy words here — think fast and look carefully!</div>

    <div class="msg" id="picMsg"></div>

    <div class="input-row">
      <input type="text" id="picInput" placeholder="Type the word…" autocomplete="off"
             onkeydown="if(event.key==='Enter')submitPictureGuess()">
      <button type="button" class="btn-primary" id="picGuessBtn" onclick="submitPictureGuess()">Guess</button>
    </div>

    <div class="btn-row">
      <button class="btn-secondary" onclick="getHint('picture')">💡 Hint (-10)</button>
      <button class="btn-ghost" onclick="startGame('picture')">🔀 Next Word</button>
      <button class="btn-primary" id="picSaveBtn" style="display:none" onclick="saveScore()">🏆 Save Score</button>
    </div>
  </div>

  <div class="leaderboard">
    <h3>🏆 Leaderboard</h3>
    <div id="leaderboardList"><div class="lb-empty">No scores yet — be the first!</div></div>
  </div>

  <footer>Made for Friday Fun · good luck, may the best guesser win 🍿</footer>
</div>

<script>
// ---------- session ----------
function getSessionId(){
  let id = localStorage.getItem('ffn_session_id');
  if(!id){
    id = 'sess-' + Math.random().toString(36).slice(2) + Date.now();
    localStorage.setItem('ffn_session_id', id);
  }
  return id;
}
const SESSION_ID = getSessionId();

async function api(path, body){
  const res = await fetch(path, {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-Session-ID': SESSION_ID},
    body: JSON.stringify(body || {})
  });
  return res.json();
}
async function apiGet(path){
  const res = await fetch(path, {headers: {'X-Session-ID': SESSION_ID}});
  return res.json();
}

// ---------- marquee bulbs ----------
(function initBulbs(){
  const bulbs = document.getElementById('bulbs');
  const count = 40;
  for(let i=0;i<count;i++){
    const s = document.createElement('span');
    const t = i / count;
    // distribute around the border rectangle
    let x, y;
    if(t < 0.25){ x = t/0.25*100; y = 0; }
    else if(t < 0.5){ x = 100; y = (t-0.25)/0.25*100; }
    else if(t < 0.75){ x = 100-(t-0.5)/0.25*100; y = 100; }
    else{ x = 0; y = 100-(t-0.75)/0.25*100; }
    s.style.left = x + '%';
    s.style.top = y + '%';
    s.style.animationDelay = (Math.random()*1.6) + 's';
    bulbs.appendChild(s);
  }
})();

// ---------- state ----------
let currentGame = null;
let currentDifficulty = 'medium';
let currentCategory = 'mixed';
const ALL_PANELS = ['numberPanel', 'wordPanel', 'picturePanel'];

function chooseGame(type){
  currentGame = type;
  document.getElementById('picker').style.display = 'none';
  ALL_PANELS.forEach(id => document.getElementById(id).classList.remove('active'));
  startGame(type);
}

function backToPicker(){
  document.getElementById('picker').style.display = 'grid';
  ALL_PANELS.forEach(id => document.getElementById(id).classList.remove('active'));
  currentGame = null;
}

function setDifficulty(diff){
  currentDifficulty = diff;
  document.querySelectorAll('#diffRow .diff-btn').forEach(b => b.classList.toggle('active', b.dataset.diff === diff));
  startGame('number');
}

function setCategory(cat){
  currentCategory = cat;
  document.querySelectorAll('#catRow .diff-btn').forEach(b => b.classList.toggle('active', b.dataset.cat === cat));
  startGame('picture');
}

async function startGame(type){
  const data = await api('/select_game', {game_type: type, difficulty: currentDifficulty, category: currentCategory});
  renderState(type, data, null);
  const panelId = type === 'number' ? 'numberPanel' : type === 'word' ? 'wordPanel' : 'picturePanel';
  document.getElementById(panelId).classList.add('active');
}

function renderState(type, state, resultMsg){
  if(type === 'number'){
    document.getElementById('numScore').textContent = state.score;
    document.getElementById('numAttempts').textContent = state.attempts;
    document.getElementById('numMaxAttempts').textContent = state.max_attempts;
    document.getElementById('numHints').textContent = state.hints_used;
    document.getElementById('numRangeHint').textContent = `Pick a number between ${state.min_range} and ${state.max_range}`;

    const msgEl = document.getElementById('numMsg');
    msgEl.className = 'msg';
    if(resultMsg){
      msgEl.textContent = resultMsg.message;
      if(resultMsg.won) msgEl.classList.add('good');
      else if(resultMsg.ok === false || resultMsg.direction) msgEl.classList.add('bad');
    } else {
      msgEl.textContent = state.message;
    }

    const hist = document.getElementById('numHistory');
    hist.innerHTML = '';
    (state.guess_history || []).forEach(g => {
      const c = document.createElement('span');
      c.className = 'chip ' + (g.result === 'correct' ? 'correct' : g.result);
      c.textContent = g.value + (g.result === 'low' ? ' ↑' : g.result === 'high' ? ' ↓' : ' ✓');
      hist.appendChild(c);
    });

    document.getElementById('numSaveBtn').style.display = state.game_over ? 'block' : 'none';

    if(state.game_over){
      document.getElementById('numInput').disabled = true;
    } else {
      document.getElementById('numInput').disabled = false;
      document.getElementById('numInput').value = '';
      document.getElementById('numInput').focus();
    }
  } else if(type === 'word'){
    document.getElementById('wordScore').textContent = state.score;
    document.getElementById('wordAttempts').textContent = state.attempts;
    document.getElementById('wordMaxAttempts').textContent = state.max_attempts;
    document.getElementById('wordHints').textContent = state.hints_used;
    document.getElementById('scrambleBox').textContent = state.scrambled_word || '…';

    const msgEl = document.getElementById('wordMsg');
    msgEl.className = 'msg';
    if(resultMsg){
      msgEl.textContent = resultMsg.message;
      if(resultMsg.won) msgEl.classList.add('good');
      else msgEl.classList.add('bad');
    } else {
      msgEl.textContent = state.hint ? '' : state.message;
    }

    document.getElementById('wordSaveBtn').style.display = state.game_over ? 'block' : 'none';

    if(state.game_over){
      document.getElementById('wordInput').disabled = true;
    } else {
      document.getElementById('wordInput').disabled = false;
      document.getElementById('wordInput').value = '';
      document.getElementById('wordInput').focus();
    }
  } else if(type === 'picture'){
    document.getElementById('picScore').textContent = state.score;
    document.getElementById('picAttempts').textContent = state.attempts;
    document.getElementById('picMaxAttempts').textContent = state.max_attempts;
    document.getElementById('picHints').textContent = state.hints_used;
    document.getElementById('picClue').textContent = state.clue || '_ _ _ _';
    document.getElementById('picCatTag').textContent = state.category_label || 'Mixed';
    const modeEl = document.getElementById('wordMode');
    const tipEl = document.getElementById('wordTip');
    if(state.mode === 'missing'){
      modeEl.textContent = '🕵️ FIND THE MISSING LETTER(S)';
      tipEl.textContent = '💭 Replace the underscore(s) and type the complete word!';
    } else {
      modeEl.textContent = '🔀 UNSCRAMBLE THE WORD';
      tipEl.textContent = '💭 No easy words here — think fast and look carefully!';
    }

    const msgEl = document.getElementById('picMsg');
    msgEl.className = 'msg';
    if(resultMsg){
      msgEl.textContent = resultMsg.message;
      if(resultMsg.won) msgEl.classList.add('good');
      else msgEl.classList.add('bad');
    } else {
      msgEl.textContent = state.message;
    }

    document.getElementById('picSaveBtn').style.display = state.game_over ? 'block' : 'none';

    if(state.game_over){
      document.getElementById('picInput').disabled = true;
    } else {
      document.getElementById('picInput').disabled = false;
      document.getElementById('picInput').value = '';
      document.getElementById('picInput').focus();
    }
  }
}

async function submitNumberGuess(){
  const input = document.getElementById('numInput');
  if(!input.value) return;
  const data = await api('/guess', {guess: input.value});
  renderState('number', data.game_state, data.result);
  updateThermo(data.result);
  if(data.result && data.result.won){
    celebrate();
  }
}

function updateThermo(result){
  const box = document.getElementById('thermo');
  const fill = document.getElementById('thermoFill');
  if(!result || result.won || !result.temperature){
    box.classList.remove('show');
    return;
  }
  box.classList.add('show');
  const scale = {
    '🔥 Blazing hot': 95, '🌶️ Very hot': 80, '☀️ Warm': 60,
    '🌤️ Cool': 40, '❄️ Cold': 20, '🧊 Freezing': 6
  };
  fill.style.width = (scale[result.temperature] || 30) + '%';
}

async function submitWordGuess(){
  const input = document.getElementById('wordInput');
  if(!input.value) return;
  const data = await api('/guess', {guess: input.value});
  renderState('word', data.game_state, data.result);
  if(data.result && data.result.won){
    celebrate();
  }
}

async function submitPictureGuess(){
  const input = document.getElementById('picInput');
  if(!input) return;
  const guess = input.value.trim();
  if(!guess){
    const msg = document.getElementById('picMsg');
    msg.className = 'msg bad';
    msg.textContent = 'Type your answer first!';
    input.focus();
    return;
  }
  try {
    const data = await api('/guess', {guess: guess});
    if(data.error){
      const msg = document.getElementById('picMsg');
      msg.className = 'msg bad';
      msg.textContent = data.error;
      return;
    }
    if(!data.game_state || !data.result){
      throw new Error('Invalid response from server');
    }
    renderState('picture', data.game_state, data.result);
    if(data.result.won){
      celebrate();
    }
  } catch(err) {
    console.error('Game 3 guess failed:', err);
    const msg = document.getElementById('picMsg');
    msg.className = 'msg bad';
    msg.textContent = 'Could not submit guess. Please try again.';
  }
}

const HINT_IDS = {
  number: {msg: 'numMsg', hints: 'numHints', score: 'numScore'},
  word:   {msg: 'wordMsg', hints: 'wordHints', score: 'wordScore'},
  picture:{msg: 'picMsg', hints: 'picHints', score: 'picScore'},
};

async function getHint(type){
  const data = await api('/hint', {});
  const ids = HINT_IDS[type];
  const msgEl = document.getElementById(ids.msg);
  msgEl.className = 'msg';
  msgEl.textContent = data.message;
  document.getElementById(ids.hints).textContent = data.game_state.hints_used;
  document.getElementById(ids.score).textContent = data.game_state.score;
}

async function saveScore(){
  let name = localStorage.getItem('ffn_player_name');
  if(!name){
    name = prompt('Nice score! Enter your name for the leaderboard:', '') || 'Anonymous';
    localStorage.setItem('ffn_player_name', name);
  }
  await api('/save_score', {player_name: name});
  loadLeaderboard();
  document.getElementById('numSaveBtn').style.display = 'none';
  document.getElementById('wordSaveBtn').style.display = 'none';
  document.getElementById('picSaveBtn').style.display = 'none';
}

async function loadLeaderboard(){
  const rows = await apiGet('/leaderboard');
  const el = document.getElementById('leaderboardList');
  if(!rows.length){
    el.innerHTML = '<div class="lb-empty">No scores yet — be the first!</div>';
    return;
  }
  const medals = ['🥇','🥈','🥉'];
  el.innerHTML = rows.map((r,i) => `
    <div class="lb-row">
      <div class="lb-rank">${medals[i] || (i+1)}</div>
      <div class="lb-name">${escapeHtml(r.player_name)} <span style="opacity:.5">· ${r.game_type === 'number' ? '🔢' : r.game_type === 'picture' ? '🔀' : '🎞️'}</span></div>
      <div class="lb-score">${r.score}</div>
    </div>
  `).join('');
}
function escapeHtml(s){
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

// ---------- win banner + confetti ----------
function celebrate(){
  const banner = document.getElementById('winBanner');
  banner.classList.add('show');
  setTimeout(() => banner.classList.remove('show'), 2200);
  fireConfetti();
}

function fireConfetti(){
  const canvas = document.getElementById('confetti-canvas');
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  const colors = ['#e8c468','#f3dfa2','#59c48a','#e2665a','#7fb8ff'];
  const pieces = Array.from({length: 140}, () => ({
    x: Math.random()*canvas.width,
    y: -20 - Math.random()*canvas.height*0.3,
    r: 4 + Math.random()*5,
    c: colors[Math.floor(Math.random()*colors.length)],
    vy: 2 + Math.random()*3,
    vx: -1.5 + Math.random()*3,
    rot: Math.random()*360,
    vr: -6 + Math.random()*12,
  }));
  let frames = 0;
  const maxFrames = 130;
  function tick(){
    frames++;
    ctx.clearRect(0,0,canvas.width, canvas.height);
    pieces.forEach(p => {
      p.x += p.vx; p.y += p.vy; p.rot += p.vr;
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rot * Math.PI/180);
      ctx.fillStyle = p.c;
      ctx.fillRect(-p.r/2, -p.r/2, p.r, p.r*0.6);
      ctx.restore();
    });
    if(frames < maxFrames){
      requestAnimationFrame(tick);
    } else {
      ctx.clearRect(0,0,canvas.width, canvas.height);
    }
  }
  tick();
}
window.addEventListener('resize', () => {
  const canvas = document.getElementById('confetti-canvas');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
});

// ---------- init ----------
loadLeaderboard();
</script>
</body>
</html>
"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
