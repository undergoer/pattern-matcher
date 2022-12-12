# repo-name

## Step 1: Build the docker container

docker build -t test-api .

## Step 2: How to run the docker file

docker run -it -p 80:80 test-api

## Step 3: Example post and response

### Example 1
#### Post:
{
  "text": "Patient reports they have diabates."
}

#### Expected response:
{
    "match": 1,
    "out": "diabetes: diabates: 88",
    "type": "fuzzy",
    "success": 1
}

### Example 2
#### Post:
{
  "text": "Patient reports they ahve diabetes."
}

#### Expected response:
{
    "match": 1,
    "out": "diabetes",
    "type": "exact",
    "success": 1
}

NOTE:
  - the format for "out" when "type" is "fuzzy" is "correct form from term list: matched string from input text: matched ratio" 
  - the format for "out" when "type" is "exact" is simply the exact match as found in the terms list
  - "type" can be "exact" or "fuzzy"
  - "success" refers to whether the call was successful, not if the match was successful -- success = 1 if the call to the matcher was made sucessfully
  - "match" refers to whether a fuzzy or exact match was detected -- if True "match" = 1, if False, "match" = 0