import csv
import os


PATH = os.path.join(os.path.dirname(__file__), "data")

def write_question(link, messageId, text):
    path = os.path.join(PATH, "question.csv")
    fields = ["questionId", "messageId", "link", "text"]

    rows = loadFileRows(path)
    questionId = len(rows) + 1

    with open(path, "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(fields)
        for row in rows:
            writer.writerow(row)
        writer.writerow([questionId, messageId, link, text])

def write_answer(link, questionId):
    path = os.path.join(PATH, "answer.csv")
    fields = ["answerId", "questionId", "link"]

    rows = loadFileRows(path)
    answerId = len(rows) + 1

    with open(path, "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(fields)
        for row in rows:
            writer.writerow(row)
        writer.writerow([answerId, questionId, link])

def get_question(questionId):
    pathQuestion = os.path.join(PATH, "question.csv")
    pathAnswer = os.path.join(PATH, "answer.csv")

    try:
        question = loadFileRows(pathQuestion)[int(questionId) - 1]
    except IndexError:
        raise

    questionDict = {
        "questionId": question[0],
        "messageId": question[1],
        "link": question[2],
        "text": question[3],
        "answers": {}
    }
    answersFile = loadFileRows(pathAnswer)
    for i in answersFile:
        if i[1] == str(questionId):
            questionDict["answers"][len(questionDict["answers"]) + 1] = i[2]
    return questionDict

def loadFileRows(path=PATH, fieldnames=True):
    with open(path, newline='') as file:
        reader = csv.reader(file)
        rows = []
        firstRow = True
        for row in reader:
            if firstRow and fieldnames:
                firstRow = False
                continue
            rows.append(row)
    return rows
