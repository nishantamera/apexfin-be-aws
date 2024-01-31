from datetime import datetime
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from django.http.response import JsonResponse

from django.contrib.auth.models import User
from dbconnect import get_db_handle, get_collection_handle
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
import requests

dbName = get_db_handle("apex-global-bank")
userCollection = get_collection_handle(dbName, "user")
accountCollection = get_collection_handle(dbName, "accounts")
investmentCollection = get_collection_handle(dbName, "investments")
investmentDetailsCollection = get_collection_handle(dbName, "investment-details")
accountTransCollection = get_collection_handle(dbName, "account-transactions")
tempTransCollection = get_collection_handle(dbName, "temp-transactions")
# payeeCollection = get_collection_handle(dbName, "payee-details")

azureABCredentials = {
    "username": "azure_api@bmc.com",
    "password": "Azure@098"
}

azureLoginEndpoint = "https://democentraldev.trybmc.com/apex-azure/account/login"
azureCCEndpoint = "https://democentraldev.trybmc.com/apex-azure/cards"
azureCCSummaryEndpoint = "https://democentraldev.trybmc.com/apex-azure/card-summary"
azureGetPayeesEndpoint = "https://democentraldev.trybmc.com/apex-azure/get-payees"
azureAddPayeeEndpoint = "https://democentraldev.trybmc.com/apex-azure/add-payee"
azureDeletePayeeEndpoint = "https://democentraldev.trybmc.com/apex-azure/delete-payee"

def search_user(email):
    user = list(userCollection.find({"email": email}))
    if(len(user)):
        return(user[0])
    else:
        return(None)


@api_view(['POST'])
# @permission_classes([IsAdminUser])
@permission_classes([AllowAny])
def signup(request):
    data = json.loads(request.body)

    firstname = data['firstname']
    lastname = data['lastname']
    email = data['email']
    dob = data['dob']
    number = data['number']
    address = data['address']
    username = data['username']
    pin = data['pin']

    try:
        if User.objects.filter(email=email).exists():
            return JsonResponse({"error": "Email already exist."}, status=400, safe=False)
        elif User.objects.filter(username=username).exists():
            return JsonResponse({"error": "Username already exist."}, status=400, safe=False) 
        else:
            User.objects.create_user(username=username, email=email, password=pin)

            userProfile = {"firstname": firstname, "lastname": lastname, "username": username, "email": email, "dateOfBirth": dob, "number": number, "address": address}
            userCollection.insert_one(userProfile)
            return JsonResponse({"success": "Account has been created"}, status=200, safe=False)
    except Exception as e:
        print(repr(e))
        return JsonResponse({"error": "Something went wrong when registering account. Please try again."}, status=400, safe=False)
    
@api_view(['POST'])
# @permission_classes([IsAdminUser])
@permission_classes([AllowAny])
def login(request):
    user = request.user
    data = request.data
    currentTime = round((datetime.now()).timestamp()*1000)
    username = data['username']
    pin = data['pin']

    try:
        user = authenticate(request, username=username, password=pin)
        if user is not None:
            refreshToken = RefreshToken.for_user(user)
            userCollection.update_one({"username": username}, {"$set": {"lastLoggedIn": currentTime}})
            return JsonResponse({"access": str(refreshToken.access_token), "refresh": str(refreshToken)}, status=200, safe=False)
        else: 
            return JsonResponse({"error": "Invalid username or password, please try again."}, status=401, safe=False)
    except:
        return JsonResponse({"error": "Something went wrong logging into account"}, status=400, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_details(request):
    user = request.user
    user = User.objects.get(id=user.id)
    if user is not None:
        userEmail = getattr(user, "email")
        searchedUser = search_user(userEmail)
        userId = searchedUser['_id']
        fullName = searchedUser['firstname'] + " " + searchedUser['lastname']
        lastLoginTime = searchedUser['lastLoggedIn']
        accounts = list(accountCollection.find({"userId": str(userId)}, {"_id": 0, "userId": 0}))
        investments = list(investmentCollection.find({"userId": str(userId)}, {"_id": 0, "userId": 0}))
        # creditCard = creditCardCollection.find_one({"userId": str(userId)}, {"_id": 0, "userId": 0})
        response, statusCode = azure_get_operation(userId, "userId", azureCCEndpoint)
        if (statusCode != 200):
            return JsonResponse({"error": response}, status=400, safe=False)
        creditCard = response
        details = {
            "User Full Name": fullName,
            "User Last Login Timestamp": lastLoginTime,
            "Accounts": accounts,
            "Investments": investments,
            "Credit-Cards": creditCard,
            "Loans": 0
        }
        # print(details)
        return JsonResponse({"success": "Successfully retrieved dashboard details.", "details": details}, status=200, safe=False)
    else:
        return JsonResponse({"error": "No such user found."}, status=404, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_investment_details(request):
    user = request.user
    user = User.objects.get(id=user.id)
    if user is not None:
        userEmail = getattr(user, "email")
        searchedUser = search_user(userEmail)
        userId = searchedUser['_id']
        investmentFunds = investmentCollection.find_one({"userId": str(userId), "category": "Funds"}, {"_id": 0, "userId": 0})
        investmentEquity = investmentCollection.find_one({"userId": str(userId), "category": "Equity"}, {"userId": 0})
        equityId = investmentEquity['_id']
        investmentEquity.pop("_id")
        investmentDetails = list(investmentDetailsCollection.find({"equityId": str(equityId)}, {"_id": 0, "equityId": 0}))
        details = {
            "Investment Details": {"Equity": investmentEquity, "Funds": investmentFunds},
            "Investment-Portfolio": investmentDetails 
        }
        return JsonResponse({"success": "Successfully retrieved investment details.", "details": details}, status=200, safe=False)
    else:
        return JsonResponse({"error": "No such user found."}, status=404, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_savings_account_details(request):
    user = request.user
    user = User.objects.get(id=user.id)
    if user is not None:
        userEmail = getattr(user, "email")
        searchedUser = search_user(userEmail)
        userId = searchedUser['_id']
        account = accountCollection.find_one({"userId": str(userId)}, {"userId": 0})
        accountId = account['_id']
        account.pop("_id")
        accountTransactions = list(accountTransCollection.find({"accountId": str(accountId)}, {"_id": 0, "accountId": 0}).sort("time", -1))
        details = {
            "Account-Details": account,
            "Savings-Account-Transactions": accountTransactions
        }
        # print(details)
        return JsonResponse({"success": "Successfully retrieved savings account details.", "details": details}, status=200, safe=False)
    else:
        return JsonResponse({"error": "No such user found."}, status=404, safe=False)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payee_details(request):
    user = request.user
    user = User.objects.get(id=user.id)
    if user is not None:
        userEmail = getattr(user, "email")
        searchedUser = search_user(userEmail)
        userId = searchedUser['_id']
        account = accountCollection.find_one({"userId": str(userId)}, {"_id": 1})
        accountId = account['_id']
        response, statusCode = azure_get_operation(accountId, "userAccountId", azureGetPayeesEndpoint)
        if (statusCode != 200):
            return JsonResponse({"error": response}, status=400, safe=False)
        payeeDetails = response
        return JsonResponse({"success": "Successfully retrieved saved payee details.", "details": payeeDetails}, status=200, safe=False)
    else:
        return JsonResponse({"error": "No such user found."}, status=404, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_credit_card_details(request):
    user = request.user
    user = User.objects.get(id=user.id)
    if user is not None:
        userEmail = getattr(user, "email")
        searchedUser = search_user(userEmail)
        userId = searchedUser['_id']
        response, statusCode = azure_get_operation(userId, "userId", azureCCSummaryEndpoint)
        if (statusCode != 200):
            return JsonResponse({"error": response}, status=statusCode, safe=False)
        creditCardSummary = response
        return JsonResponse({"success": "Successfully retrieved credit card details.", "details": creditCardSummary}, status=200, safe=False)
    else:
        return JsonResponse({"error": "No such user found."}, status=404, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_details(request):
    user = request.user
    user = User.objects.get(id=user.id)
    if user is not None:
        userEmail = getattr(user, "email")
        searchedUser = search_user(userEmail)
        searchedUser.pop('_id')
        details = {
            "User-Details": searchedUser
        }
        return JsonResponse({"success": "Successfully retrieved user details.", "details": details}, status=200, safe=False)
    else:
        return JsonResponse({"error": "No such user found."}, status=404, safe=False)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_payee(request):
    user = request.user
    data = request.data
    bankName = data['bankName']
    type = data['type']
    accountNumber = data['bankAccountNumber']
    name = data['payeeName']

    if (bankName == None or type == None or accountNumber == None or name == None):
        return JsonResponse({"error": "Empty fields are not allowed."}, status=400, safe=False)
    user = User.objects.get(id=user.id)
    if user is not None:
        userEmail = getattr(user, "email")
        searchedUser = search_user(userEmail)
        userId = searchedUser['_id']
        account = accountCollection.find_one({"userId": str(userId)}, {"_id": 1})
        accountId = account['_id']
        # payee = payeeCollection.find_one({"bankAccountNumber": accountNumber}, {"_id": 0})
        # if payee == None:
        payeeDetails = {"name": name, "bankName": bankName, "accountNumber": accountNumber, "type": type, "accountId": str(accountId)}
        response, statusCode = add_payee_to_azure(payeeDetails)
        responseJson = json.loads(response)
        return JsonResponse(responseJson, status=statusCode, safe=False)
        # else:
        #     return JsonResponse({"error": "Payee already added."}, status=200, safe=False)
    else:
        return JsonResponse({"error": "No such user found."}, status=404, safe=False)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_payee(request):
    user = request.user
    data = request.data
    user = User.objects.get(id=user.id)
    if user is not None:
        accountNumber = data['bankAccountNumber']
        response, statusCode = delete_payee_from_azure(accountNumber)
        responseJson = json.loads(response)
        return JsonResponse(responseJson, status=statusCode, safe=False)
    else:
        return JsonResponse({"error": "No such user found."}, status=404, safe=False)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_transaction(request):
    user = request.user
    data = request.data
    currentTime = datetime.now()
    # currentTime = round((datetime.now()).timestamp()*1000)
    user = User.objects.get(id=user.id)
    if user is not None:
        userEmail = getattr(user, "email")
        searchedUser = search_user(userEmail)
        userId = searchedUser['_id']
        account = accountCollection.find_one({"userId": str(userId)}, {})
        accountId = account['_id']
        transactionDetails = data['transactionDetails']
        amount = data['amount']
        type = data['transactionType']

        transaction = {"accountId": str(accountId), "transactionDetails": transactionDetails, "time": currentTime, "type": type, "amount": str(amount)}
        tempTransCollection.insert_one(transaction)
        # accountTransCollection.insert_one(transaction)
        # filter = {"userId": str(userId)}
        # balance = account['balance']
        # if (type == "Deduction"):
        #     newBalance = float(balance) - float(amount)
        # elif (type == "Addition"):
        #     newBalance = float(balance) + float(amount)
        # accountCollection.update_one(filter, {"$set":{"balance": str(newBalance)}})
        return JsonResponse({"success": "Transfer success."}, status=200, safe=False)
    else:
        return JsonResponse({"error": "No such user found."}, status=404, safe=False)

def azure_login():
    credentials = json.dumps(azureABCredentials)
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(azureLoginEndpoint, headers=headers, data=credentials)
    if(response.status_code != 200):
        return(response.text, response.status_code)
    responseJson = json.loads(response.text)
    jsonWebToken = responseJson['access']
    return (jsonWebToken, 200)

def add_payee_to_azure(payeeDetails):
    response, statusCode = azure_login()
    if(statusCode != 200):
        return(response, statusCode)
    authToken = response
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + authToken
    }
    payload = json.dumps(payeeDetails)
    ccResponse = requests.post(azureAddPayeeEndpoint, headers=headers, data=payload)
    return(ccResponse.text, ccResponse.status_code)

def delete_payee_from_azure(accountNumber):
    response, statusCode = azure_login()
    if(statusCode != 200):
        return(response, statusCode)
    authToken = response
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + authToken
    }
    payload = json.dumps({
        "bankAccountNumber": str(accountNumber)
    })
    ccResponse = requests.post(azureDeletePayeeEndpoint, headers=headers, data=payload)
    return(ccResponse.text, ccResponse.status_code)

def azure_get_operation(userId, payloadType, endpoint):
    response, statusCode = azure_login()
    if(statusCode != 200):
        return(response, statusCode)
    authToken = response
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + authToken
    }
    payload = json.dumps({
        "{payloadType}".format(payloadType=payloadType): str(userId)
    })
    azureResponse = requests.get(endpoint, headers=headers, data=payload)
    if azureResponse.status_code != 200:
        return(azureResponse.text, azureResponse.status_code)
    responseJson = json.loads(azureResponse.text)
    details = responseJson['details']
    return(details, 200)

def azure_get_operation(userId, payloadType, endpoint):
    response, statusCode = azure_login()
    if(statusCode != 200):
        return(response, statusCode)
    authToken = response
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + authToken
    }
    payload = json.dumps({
        "{payloadType}".format(payloadType=payloadType): str(userId)
    })
    azureResponse = requests.get(endpoint, headers=headers, data=payload)
    if azureResponse.status_code != 200:
        return(azureResponse.text, azureResponse.status_code)
    responseJson = json.loads(azureResponse.text)
    details = responseJson['details']
    return(details, 200)

