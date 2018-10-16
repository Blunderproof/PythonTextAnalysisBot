import praw
import time
import sys
import threading
import csv
import os
import re


commentID_Dict = {} #CAPTURES THE IDS FROM THAT INSTANCE OF THE CHECK
commentScore_Dict = {}
commentID_List = []
commentObjectList = []
allCommentIDs_Dict = {} #CAPTURES THE NUMBERS OF APPEARANCES OF ALL COMMENTS WITHIN THE COUNT SIZE
threadsDict = {}




class myComment:
    heightDict = {}
    def __init__(self, commentID, commentBody, commentScore, commentFoundTime):
        self.ID = commentID
        self.timeFound = commentFoundTime
        self.body = commentBody
        self.score = commentScore

    def __str__(self):
        self_description = 'ID: %s, Score: %s, Time Found: %s' % (self.ID, self.score, self.timeFound)
        return self_description
    def updateHeightCounter(self, height, heightDict=None):
        if height in heightDict:
            heightDict[height] += 1
        else:
            heightDict.update({height : 1})


#https://www.youtube.com/watch?v=Uvxu2efXuiY THESE ARE NECESSARY DATA MEMBERS FOR THE ACCOUNT LOGIN
user_name = 'CallerNumber4'
app_ua = '/u/CallerNumber4 Text Analysis for Class'
app_secret = ''
app_id = ''
app_uri = 'https://127.0.0.1:65010/authorize_callback'
app_scopes = 'account creddits edit flair history identity livemanage modconfig modcontributors modflair modlog modothers modposts modself modwiki mysubreddits privatemessages read report save submit subscribe vote wikiedit wikiread'
app_account_code = ''
app_refresh_token = ''

#collects thread-IDs for a set number of threads for a particular subreddit.
def collectSubredditThreads(subreddit_Name, numberOfThreads, threadsDict):
    subreddit=r.get_subreddit(subreddit_Name)
    #Only collects relatively popular threads. Collects a normalizing value of the thread strength to account for especially popular subreddits
    boolDidNotFinishEarly = False
    minValueOfThread = 300
    maxValueOfThread = 7000
    print("Collecting threads with karma of at least: " + str(minValueOfThread) + " but less than: " + str(maxValueOfThread))
    for submission in subreddit.get_top():
        if submission.score > minValueOfThread and submission.score < maxValueOfThread:
            threadsDict.update({submission.id : submission.score})
            print(submission.id)
            numberOfThreads-=1
        if numberOfThreads <= 0:
            boolDidNotFinishEarly = True
            break
    if boolDidNotFinishEarly == False:
        print("FINISHED COLLECTING THREADS EARLY!!!!!!!!")
        #limit=numberOfThreads

#Updates the subreddit CSV from the word/word strength dictionary
def updateSubredditCSV(subreddit_Name, threadWordScoreDict, threadWordsFreqDict, threadStrength):
    file_str = subreddit_Name + ".csv"

    if os.path.isfile(file_str) == False:
        print("No file found for that subreddit, creating one now.")
        file = open(file_str, 'w+')
        file.close()
         ###FINISH HERE <-------
    if os.path.getsize(file_str) > 2:
        updateNonEmpty(subreddit_Name, threadWordScoreDict, threadWordsFreqDict, threadStrength)

    else:
        updateEmpty(subreddit_Name, threadWordScoreDict, threadWordsFreqDict, threadStrength)


def updateEmpty(subreddit_Name, threadWordScoreDict, threadWordsFreqDict, threadStrength):
    file_str = subreddit_Name + ".csv"

    print("UPDATE_CSV found an empty CSV")
    with open(file_str, 'w+', encoding='utf-8', errors='ignore') as csv_file:
        for key, value in threadWordScoreDict.items():
            freqCount = threadWordsFreqDict[key]
            valueNormalized = value / threadStrength
            csv_file.write(str(key) + "," + str(valueNormalized) + "," + str(freqCount) + "\n")
            #print(str(key) + "," + str(value) + "," + str(freqCount) + "\n")


def updateNonEmpty(subreddit_Name, threadWordScoreDict, threadWordsFreqDict, threadStrength):
    file_str = subreddit_Name + ".csv"

    CSV_wordsDictScore = {}
    CSV_wordsDictFreq = {}
    totalWordFreqDict = {}
    totalWordScoreDict = {}

    print("UPDATE_CSV found a non-empty CSV")
    with open(file_str) as csv_file:
        #Creates a dictionary of the words/word score of words already in the CSV
        csv_reader = csv.reader(csv_file, delimiter=',', quotechar='|')

        for row in csv_reader:
            CSV_wordsDictScore.update({row[0] : row[1]})
            CSV_wordsDictFreq.update({row[0] : row[2]})
        #for key, value in CSV_wordsDictScore.items():
            #print("KEY: " + str(key) + " -- SCORE: " + str(value))

        threadWordScoreList = threadWordScoreDict.keys()
        CSV_wordsList = CSV_wordsDictScore.keys()


        for word in threadWordScoreList:
            #Adds values for duplicate words found across threads
            if word in CSV_wordsList:
                thread_wordScore = threadWordScoreDict[word] / threadStrength #Score from the most recent thread
                CSV_wordScore = CSV_wordsDictScore[word]    #score saved in the csv
                wordScore = float(thread_wordScore) + float(CSV_wordScore)

                thread_wordFreq = threadWordsFreqDict[word]
                CSV_wordFreq = CSV_wordsDictFreq[word]
                wordFreq = int(thread_wordFreq) + float(CSV_wordFreq)

                totalWordScoreDict.update({word : wordScore})
                totalWordFreqDict.update({word : wordFreq})
            #Allows new words to be added
            else:
                totalWordScoreDict.update({word : (threadWordScoreDict[word] / threadStrength)})
                totalWordFreqDict.update({word : threadWordsFreqDict[word]})

    with open(file_str, 'w+', encoding='utf-8', errors='ignore') as csv_file:
        for key, value in totalWordScoreDict.items():
            freqCount = totalWordFreqDict[key]
            if key.isalnum():
                csv_file.write(str(key) + "," + str(value) + "," + str(freqCount) + "\n")

#updates the dictionary from the comments of the thread
def updatethreadWordScoreDict(commentObjectList, threadWordScoreDict, threadWordsFreqDict):
    for comment in commentObjectList:
        for word in comment.body.split():
            wordCleaned = ''.join(e for e in word if e.isalnum())
            if word in threadWordScoreDict.keys():
                threadWordScoreDict[wordCleaned]+= comment.score
                threadWordsFreqDict[wordCleaned]+= 1
            else:
                threadWordScoreDict.update({str(wordCleaned) : comment.score})
                threadWordsFreqDict.update({str(wordCleaned) : 1})



def uprint(*objects, sep=' ', end='\n', file=sys.stdout): #ALLOWS USER TO PRINT OUT COMMENTS PROPERLY
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file)


def subredditCSV_WordUsageComparison(subreddit_Name_1, subreddit_Name_2):
    print("Comparing Subreddits: " + subreddit_Name_1 + " and " + subreddit_Name_2)
    file_str1 = subreddit_Name_1 + ".csv"
    file_str2 = subreddit_Name_2 + ".csv"
    file_cmpStr = subreddit_Name_1 + "-vs.-" + subreddit_Name_2 + ".csv"
    CSV1_wordsDictScore = {}
    CSV2_wordsDictScore = {}
    CSV1_wordsDictFreq = {}
    CSV2_wordsDictFreq = {}
    differenceStrengthDict = {}
    combinedWordsDict = []
    #CSV1_wordsList = []
    #CSV2_wordsList = []
    #if os.path.isfile(file_str1) or os.path.isfile(file_str2) == False:
    #    print("ERROR: One of the .csvs didn't exist!")
    #    return


    with open(file_str1, 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',', quotechar='|')
        for row in csv_reader:
                CSV1_wordsDictScore.update({row[0] : row[1]})
                CSV1_wordsDictFreq.update({row[0] : row[2]})

    with open(file_str2, 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',', quotechar='|')
        for row in csv_reader:
                CSV2_wordsDictScore.update({row[0] : row[1]})
                CSV2_wordsDictFreq.update({row[0] : row[2]})
    CSV1_wordsList = list(CSV1_wordsDictScore.keys())
    CSV2_wordsList = list(CSV2_wordsDictScore.keys())
    combinedWordsList = (CSV2_wordsList + CSV1_wordsList)
    for word in combinedWordsList:
        if (word in CSV1_wordsList and word in CSV2_wordsList):
            CSV1_wordStrength = float(CSV1_wordsDictScore[word]) / float(CSV1_wordsDictFreq[word])
            #print("CSV1 WORD STRENGTH: " + str(CSV1_wordStrength) + "CSV2_wordsDictScore[word]: " + str(CSV2_wordsDictScore[word]) + " CSV2_wordsDictFreq[word]" + str(CSV2_wordsDictFreq[word]))
            CSV2_wordStrength = float(CSV2_wordsDictScore[word]) / float(CSV2_wordsDictFreq[word])
            if CSV2_wordStrength != 0:
                wordStrengthDifference = float(CSV1_wordStrength / CSV2_wordStrength)
                differenceStrengthDict.update({word : wordStrengthDifference})
        
        # elif word in CSV1_wordsList:
        #     print("FOUND WORD ONLY IN LIST 1!!!!!!!!!!!!!!!")
        #     CSV1_wordStrength = float(CSV1_wordsDictScore[word]) / float(CSV1_wordsDictFreq[word])
        #     CSV2_wordStrength = 1
        #     if CSV2_wordStrength != 0:
        #         wordStrengthDifference = float(CSV1_wordStrength / CSV2_wordStrength)
        #         differenceStrengthDict.update({word : wordStrengthDifference})
        # elif word in CSV2_wordsList:
        #     print("FOUND WORD ONLY IN LIST 2!!!!!!!!!!!!!!!")
        #     CSV1_wordStrength = 1
        #     CSV2_wordStrength = float(CSV2_wordsDictScore[word]) / float(CSV2_wordsDictFreq[word])
        #     if CSV2_wordStrength != 0:
        #         wordStrengthDifference = float(CSV1_wordStrength / CSV2_wordStrength)
        #         differenceStrengthDict.update({word : wordStrengthDifference})
        # else:
        #     print("YOU BROKE THIS THANG")

    with open(file_cmpStr, 'w+', encoding='utf-8', errors='ignore') as csv_file:
        csv_file.write("Word: " + "," + "Strength: \n" )
        for word in differenceStrengthDict.keys():
            csv_file.write(str(word) + "," + str(differenceStrengthDict[word]) + "\n")



def getTopCommentsFromThread(thread_id, commentCount, commentID_Dict, repeatCount, startTime):
    submission = r.get_submission(submission_id=thread_id)
    comments = []
    comments = submission.comments
    #flat_comments = praw.helpers.flatten_tree(submission.comments)
    #flat_comments.sort(key=lambda comment: comment.score, reverse=True)
    caught = set()
    number = 1
    for top_level_comment in comments:

        if not hasattr(top_level_comment, 'body'):
            continue
        caught.add(top_level_comment.id)
        commentID_Dict.update({str(top_level_comment.id) : number})
        if top_level_comment not in commentID_List:
            commentID_List.append(top_level_comment.id)
            timeFound = time.time() - startTime
            #Creates an object of type myComment and appends it to the list
            commentObjectList.append(createNewCommentObject(top_level_comment.id, top_level_comment.body, top_level_comment.score, timeFound))
        #else :
        #    commentScore_Dict[top_level_comment.id] = top_level_comment.score
        number+=1
        #uprint("***COMMENT***\n" + top_level_comment.body + '\n' + "COMMENT SCORE: " + str(top_level_comment.score) + '\n') #PRINTS THE TOP COMMENTS OF THREAD
        #Decrement comment count. If you want to collect more comments set the initial parameter higher in this function.
        commentCount-=1
        if (commentCount <= 0):
            break
    #print("PLACEMENT COUNTS FOR COMMENT IDs: " + str(commentID_Dict) + '\n' + "COMMENT SCORES: " + str(commentScore_Dict) + '\n' + str(repeatCount - 1) + " INSTANCES LEFT")


#Creates a new object of the myComment class with the name being the commentID
def createNewCommentObject(comment_ID, commentBody, commentScore, timeFound):
    return myComment(comment_ID, commentBody, commentScore, timeFound)

#Updates a dictionary of all comments found. Increments if found again. Sets to 1 if found for the first time and appends to the dictionary.
def queryCommentPositions(commentID_Dict, allCommentIDs_Dict):
    for commentID in commentID_Dict:
        if(commentID in allCommentIDs_Dict):
            allCommentIDs_Dict[commentID]+=1
        else:
            allCommentIDs_Dict.update({commentID : 1 })

    #print("COMMENT COUNT FOR ALL COMMENTS: " + str(allCommentIDs_Dict))

#Simply finds the oldest and newest comments in the post
def findOldestCommentInDict(allCommentIDs_Dict):
    #commentObjects = [myComment(*params) for params in zip (commentID, commentBody, commentScore, commentFoundTime)] #FIX LATER!!!!!!!!!!!!<<<<------------- http://stackoverflow.com/questions/17679809/how-to-print-out-str-for-each-instance-of-a-class-in-a-loop
    #for comment in commentObjectList:
    #    print(comment)
    r = sorted(allCommentIDs_Dict, key=lambda item: (int(item.partition(' ')[0])
        if item[0].isdigit() else float('inf'), item))
    #print(str(r[0]) + " is the first comment. " + str(r[-1]) + " is the last one")

# def checkTopComments(subreddit_Name):
#     subreddit = r.get_subreddit(subreddit_Name)
#     for submission in subreddit.get_hot(limit=10):
#         submissionCommentsHot = submission.get_comments(params={'t': 'all'}, limit=25)
#         print(submissionCommentsHot)
#     #Collect the id's for the top 3 comments. Save the time stamp.
#     #Repeat at certain intervals. Compare the id's for the current top comments. If they change track how often.

#THIS IS THE MAIN FUNCTION IT'S USING
def checkForVariantionInTopComments(subreddit_Name, thread_id, commentCount, repeatCount, commentID_Dict, allCommentIDs_Dict, threadStrength):
    threadWordScoreDict = {}
    threadWordsFreqDict = {}


    startTime = time.time()
    getTopCommentsFromThread(thread_id, commentCount, commentID_Dict, repeatCount, startTime)
    #queryCommentPositions(commentID_Dict, allCommentIDs_Dict)
    #repeatCount-=1
    #findOldestCommentInDict(allCommentIDs_Dict)
    updatethreadWordScoreDict(commentObjectList, threadWordScoreDict, threadWordsFreqDict)
    updateSubredditCSV(subreddit_Name, threadWordScoreDict, threadWordsFreqDict, threadStrength)

#Logs into the praw api
def login():
    r = praw.Reddit(app_ua)
    r.set_oauth_app_info(app_id, app_secret, app_uri)
    r.refresh_access_information(app_refresh_token)
    return r

###########-----------------------START PROGRAM HERE--------------#######
r = login()
if (str(r.user) == user_name):
    print("Login successful for: " + str(r.user) + "\n")
subreddit_Name_1 = 'pics'
subreddit_Name_2 = 'mildlyinteresting'
numberOfThreads = 20
numberOfComments = 6
#subreddit_Name, commentCount, repeatCount, commentID_Dict, allCommentIDs_Dict, normalizingValue
collectSubredditThreads(subreddit_Name_1, numberOfThreads, threadsDict)
for thread in threadsDict.keys():
    threadStrength = threadsDict[thread]
    print(threadStrength)
    checkForVariantionInTopComments(subreddit_Name_1, thread, numberOfComments, 1, commentID_Dict, allCommentIDs_Dict, threadStrength)

commentID_Dict.clear() #CAPTURES THE IDS FROM THAT INSTANCE OF THE CHECK
allCommentIDs_Dict.clear() #CAPTURES THE NUMBERS OF APPEARANCES OF ALL COMMENTS WITHIN THE COUNT SIZE
threadsDict.clear()
commentObjectList.clear()

collectSubredditThreads(subreddit_Name_2, numberOfThreads, threadsDict)
for thread in threadsDict.keys():
    threadStrength = threadsDict[thread]
    print(threadStrength)
    checkForVariantionInTopComments(subreddit_Name_2, thread, numberOfComments, 1, commentID_Dict, allCommentIDs_Dict, threadStrength)

subredditCSV_WordUsageComparison(subreddit_Name_1, subreddit_Name_2)
