from pymongo import MongoClient
from multiprocessing import Process
from commonpyutils import guiutils
import os, copy

devmongoClient = MongoClient(os.environ["MONGODEV_INSTANCE"])
devMongodbHandle = devmongoClient["admin"]
devMongodbHandle.authenticate(os.environ["MONGODEV_UNAME"], os.environ["MONGODEV_PASS"])
unencoded_resultCollHandle = devmongoClient["eva_testing"]["sample_unenc"]
encoded_resultCollHandle = devmongoClient["eva_testing"]["sample_enc"]

client = MongoClient(guiutils.promptGUIInput("MongoDB Production Host:", "MongoDB Production Host:"))
mongodbHandle = client["admin"]
mongodbHandle.authenticate(guiutils.promptGUIInput("MongoDB Production User:", "MongoDB Production User:"),
                           guiutils.promptGUIInput("MongoDB Production Password:", "MongoDB Production Password:", "*"))

mongodbHandle = client["eva_hsapiens_grch37"]
srcCollHandle_grch37 = mongodbHandle["variants_1_2"]
filesCollHandle_grch37 = mongodbHandle["files_1_2"]
filesCache = list(filesCollHandle_grch37.find())
filesCacheLookup = {}
for doc in filesCache:
    filesCacheLookup[doc["fid"] + "_" + doc["sid"]] = doc

chromosome_LB_UB_Map = [{ "_id" : "1", "minStart" : 10020, "maxStart" : 249240605, "numEntries" : 12422239 },
{ "_id" : "2", "minStart" : 10133, "maxStart" : 243189190, "numEntries" : 13217397 },
{ "_id" : "3", "minStart" : 60069, "maxStart" : 197962381, "numEntries" : 10891260 },
{ "_id" : "4", "minStart" : 10006, "maxStart" : 191044268, "numEntries" : 10427984 },
{ "_id" : "5", "minStart" : 10043, "maxStart" : 180905164, "numEntries" : 9742153 },
{ "_id" : "6", "minStart" : 61932, "maxStart" : 171054104, "numEntries" : 9340928 },
{ "_id" : "7", "minStart" : 10010, "maxStart" : 159128653, "numEntries" : 8803393 },
{ "_id" : "8", "minStart" : 10059, "maxStart" : 146303974, "numEntries" : 8458842 },
{ "_id" : "9", "minStart" : 10024, "maxStart" : 141153428, "numEntries" : 6749462 },
{ "_id" : "10", "minStart" : 60222, "maxStart" : 135524743, "numEntries" : 7416994 },
{ "_id" : "11", "minStart" : 61248, "maxStart" : 134946509, "numEntries" : 7690584 },
{ "_id" : "12", "minStart" : 60076, "maxStart" : 133841815, "numEntries" : 7347630 },
{ "_id" : "13", "minStart" : 19020013, "maxStart" : 115109865, "numEntries" : 5212835 },
{ "_id" : "14", "minStart" : 19000005, "maxStart" : 107289456, "numEntries" : 4989875 },
{ "_id" : "15", "minStart" : 20000003, "maxStart" : 102521368, "numEntries" : 4607392 },
{ "_id" : "16", "minStart" : 60008, "maxStart" : 90294709, "numEntries" : 5234679 },
{ "_id" : "17", "minStart" : 47, "maxStart" : 81195128, "numEntries" : 4652428 },
{ "_id" : "18", "minStart" : 10005, "maxStart" : 78017157, "numEntries" : 4146560 },
{ "_id" : "19", "minStart" : 60360, "maxStart" : 59118925, "numEntries" : 3821659 },
{ "_id" : "20", "minStart" : 60039, "maxStart" : 62965384, "numEntries" : 3512381 },
{ "_id" : "21", "minStart" : 9411199, "maxStart" : 48119868, "numEntries" : 2082680 },
{ "_id" : "22", "minStart" : 16050036, "maxStart" : 51244515, "numEntries" : 2172028 },
{ "_id" : "X", "minStart" : 60003, "maxStart" : 155260479, "numEntries" : 5893713 },
{ "_id" : "Y", "minStart" : 10003, "maxStart" : 59363485, "numEntries" : 504508 }]

def hexencode(sampleIndexSet, numSamp):
    hexLookup = {'0000': 0, '0001': 1,'0010': 2,'0011': 3,'0100': 4,'0101': 5,'0110': 6,'0111': 7,
                 '1000': 8,'1001': 9,'1010': 10,'1011': 11,'1100': 12,'1101': 13,'1110': 14,'1111': 15}
    bitArray = ['0']*numSamp
    extraAlloc = 0
    if numSamp%4 > 0: extraAlloc = 1
    resultArray = ['']*((numSamp/4)+extraAlloc)
    for elem in sampleIndexSet:
        bitArray[elem] = '1'
    bitArray = ''.join(bitArray)
    for i in range(0,numSamp,4):
        lookupVal = bitArray[i:i+4]
        if i + 4 > numSamp: lookupVal = lookupVal.zfill(4)
        resultArray[i/4] = hexLookup[lookupVal]
    return resultArray


for entry in chromosome_LB_UB_Map:
    chromosome = entry["_id"]
    lowerBound = entry["minStart"]
    upperBound = entry["maxStart"]
    query = {"chr": chromosome, "start": {"$gte": lowerBound, "$lte": upperBound}, "files.samp": {"$exists": "true"}}
    results = list(srcCollHandle_grch37.find(query).limit(100))
    for variantDoc in results:
        originalDoc = copy.deepcopy(variantDoc)
        filesDocs = variantDoc["files"]
        filesDocIndex = 0
        for filesDoc in filesDocs:
            if ("fid" not in filesDoc) or ("sid" not in filesDoc): continue
            fid = filesDoc["fid"]
            sid = filesDoc["sid"]
            fileCache = filesCacheLookup[fid + "_" + sid]
            if ("st" not in fileCache) or ("samp" not in fileCache): continue
            numSamp = fileCache["st"]["nSamp"]
            sampleDoc = filesDoc["samp"]
            defaultGenotypeSampleSet = set(range(0,numSamp))
            defaultGenotype = None
            for sampleKey in sampleDoc:
                if sampleKey == "def":
                    defaultGenotype = sampleDoc[sampleKey]
                else:
                    sampleIndexSet = set(sampleDoc[sampleKey])
                    defaultGenotypeSampleSet = defaultGenotypeSampleSet - sampleIndexSet
                    sampleDoc[sampleKey] = hexencode(sampleIndexSet, numSamp)
            #del sampleDoc["def"]
            #sampleDoc[defaultGenotype] = hexencode(defaultGenotypeSampleSet, numSamp)
            filesDoc["samp"] = sampleDoc
            filesDocs[filesDocIndex] = filesDoc
            filesDocIndex += 1

        unencoded_resultCollHandle.insert(originalDoc)
        variantDoc["files"] = filesDocs
        encoded_resultCollHandle.insert(variantDoc)