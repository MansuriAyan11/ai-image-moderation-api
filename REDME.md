API Testing Summary

Endpoint: GET /
Method: GET
Result: API health check working
Status Code: 200 OK

Endpoint: POST /detect
Method: POST
Input: Safe image
Result: Image marked safe
Status Code: 200 OK

Endpoint: POST /detect
Method: POST
Input: Unsafe image
Result: Inappropriate content detected
Status Code: 200 OK

Endpoint: POST /detect
Method: POST
Input: .txt file
Result: Invalid file extension rejected
Status Code: 400 Bad Request

Endpoint: POST /detect
Method: POST
Input: No file
Result: Required file validation error
Status Code: 422 Unprocessable Entity