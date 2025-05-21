# Receipt OCR System

This application is an automated system for extracting information from scanned receipts using OCR and AI techniques. It processes PDF receipts and stores the extracted data in a structured SQLite database.

## Features

- Upload PDF receipts via REST API
- Validate PDF files
- Extract key receipt details using OCR/AI text extraction
- Store extracted data in a structured SQLite database
- Manage and retrieve receipts via REST APIs

## Tech Stack

- **Backend**: Python, Flask
- **Database**: SQLite with SQLAlchemy ORM
- **OCR/AI**: PyTesseract, PDF2Image, SpaCy NLP
- **PDF Processing**: PyPDF2

## Setup and Installation

### Prerequisites

- Python 3.12.3
- Poetry 2.1.2
- Tesseract OCR engine installed on your system
- Poppler (required for pdf2image)

### Installation Steps

1. Clone the repository:
   ```
   git clone https://github.com/Amandeep18-tech/receipt-processor.git
   ```

2. Install Poppler:
    ```
    sudo apt update
    sudo apt install poppler-utils
    ```

3. Install Tesseract:
    ```
    sudo apt update
    sudo apt install tesseract-ocr
    ```

4. Install dependencies from poetry
    ```
    poetry install
    poetry env activate
    ```

6. Run the application:
   ```
   poetry run python main.py
   ```

The server will start at http://localhost:5000

## Database Schema

The application uses a SQLite database (`receipts.db`) with the following structure:

### `receipt_file` Table
Stores metadata of uploaded receipt files.

| Column Name     | Description                                              |
|-----------------|----------------------------------------------------------|
| `id`            | Unique identifier (UUID)                                 |
| `file_name`     | Name of the uploaded file                                |
| `file_path`     | Storage path of the file                                 |
| `is_valid`      | Boolean indicating if file is a valid PDF                |
| `invalid_reason`| Reason for file being invalid (if applicable)            |
| `is_processed`  | Boolean indicating if file has been processed            |
| `created_at`    | Timestamp when receipt was uploaded                      |
| `updated_at`    | Timestamp of latest modification                         |

### `receipt` Table
Stores extracted information from valid receipt files.

| Column Name     | Description                                              |
|-----------------|----------------------------------------------------------|
| `id`            | Unique identifier (UUID)                                 |
| `receipt_file_id`| Foreign key to the associated receipt_file              |
| `purchased_at`  | Date and time of purchase (extracted)                    |
| `merchant_name` | Merchant name (extracted)                                |
| `total_amount`  | Total amount spent (extracted)                           |
| `currency`      | Currency used (extracted)                                |
| `payment_method`| Payment method used (extracted)                          |
| `tax_amount`    | Tax amount (extracted)                                   |
| `receipt_number`| Receipt or invoice number (extracted)                    |
| `file_path`     | Path to the associated scanned receipt                   |
| `created_at`    | Timestamp when receipt was processed                     |
| `updated_at`    | Timestamp of latest modification                         |

### `receipt_item` Table
Stores individual items from receipts (if extractable).

| Column Name     | Description                                              |
|-----------------|----------------------------------------------------------|
| `id`            | Unique identifier (UUID)                                 |
| `receipt_id`    | Foreign key to the associated receipt                    |
| `item_name`     | Name of the purchased item                               |
| `quantity`      | Quantity purchased                                       |
| `unit_price`    | Price per unit                                           |
| `total_price`   | Total price for the item                                 |
| `created_at`    | Timestamp when item was created                          |

## API Documentation

### 1. Upload Receipt (`/upload`)

**Method**: POST  
**Content-Type**: multipart/form-data  
**Body**: 
- `file`: PDF file to upload

**Response**:
```json
{
  "message": "File uploaded successfully",
  "receipt_file": {
    "id": "uuid-string",
    "file_name": "receipt.pdf",
    "file_path": "uploads/unique-filename.pdf",
    "is_valid": true,
    "invalid_reason": null,
    "is_processed": false,
    "created_at": "2023-10-15T12:34:56.789Z",
    "updated_at": "2023-10-15T12:34:56.789Z"
  }
}
```

### 2. Validate Receipt (`/validate`)

**Method**: POST  
**Content-Type**: application/json  
**Body**:
```json
{
  "receipt_file_id": "uuid-string"
}
```

**Response**:
```json
{
  "message": "File validated",
  "is_valid": true,
  "invalid_reason": null,
  "receipt_file": {
    "id": "uuid-string",
    "file_name": "receipt.pdf",
    "file_path": "uploads/unique-filename.pdf",
    "is_valid": true,
    "invalid_reason": null,
    "is_processed": false,
    "created_at": "2023-10-15T12:34:56.789Z",
    "updated_at": "2023-10-15T12:34:56.789Z"
  }
}
```

### 3. Process Receipt (`/process`)

**Method**: POST  
**Content-Type**: application/json  
**Body**:
```json
{
  "receipt_file_id": "uuid-string"
}
```

**Response**:
```json
{
  "message": "Receipt processed successfully",
  "receipt": {
    "id": "uuid-string",
    "receipt_file_id": "uuid-string",
    "purchased_at": "2023-09-10T14:23:45.000Z",
    "merchant_name": "ACME Supermarket",
    "total_amount": 42.99,
    "currency": "USD",
    "payment_method": "Credit Card",
    "tax_amount": 3.45,
    "receipt_number": "INV-12345",
    "file_path": "uploads/unique-filename.pdf",
    "created_at": "2023-10-15T12:35:12.345Z",
    "updated_at": "2023-10-15T12:35:12.345Z",
    "items": [
      {
        "id": "uuid-string",
        "receipt_id": "uuid-string",
        "item_name": "Milk",
        "quantity": 2,
        "unit_price": 3.99,
        "total_price": 7.98,
        "created_at": "2023-10-15T12:35:12.345Z"
      },
      {
        "id": "uuid-string",
        "receipt_id": "uuid-string",
        "item_name": "Bread",
        "quantity": 1,
        "unit_price": 4.50,
        "total_price": 4.50,
        "created_at": "2023-10-15T12:35:12.345Z"
      }
    ]
  },
  "receipt_file": {
    "id": "uuid-string",
    "file_name": "receipt.pdf",
    "file_path": "uploads/unique-filename.pdf",
    "is_valid": true,
    "invalid_reason": null,
    "is_processed": true,
    "created_at": "2023-10-15T12:34:56.789Z",
    "updated_at": "2023-10-15T12:35:12.345Z"
  }
}
```

### 4. List All Receipts (`/receipts`)

**Method**: GET  
**Content-Type**: application/json  

**Response**:
```json
{
  "receipts": [
    {
      "id": "uuid-string",
      "receipt_file_id": "uuid-string",
      "purchased_at": "2023-09-10T14:23:45.000Z",
      "merchant_name": "ACME Supermarket",
      "total_amount": 42.99,
      "currency": "USD",
      "payment_method": "Credit Card",
      "tax_amount": 3.45,
      "receipt_number": "INV-12345",
      "file_path": "uploads/unique-filename.pdf",
      "created_at": "2023-10-15T12:35:12.345Z",
      "updated_at": "2023-10-15T12:35:12.345Z",
      "items": [
        {
          "id": "uuid-string",
          "receipt_id": "uuid-string",
          "item_name": "Milk",
          "quantity": 2,
          "unit_price": 3.99,
          "total_price": 7.98,
          "created_at": "2023-10-15T12:35:12.345Z"
        },
        {
          "id": "uuid-string",
          "receipt_id": "uuid-string",
          "item_name": "Bread",
          "quantity": 1,
          "unit_price": 4.50,
          "total_price": 4.50,
          "created_at": "2023-10-15T12:35:12.345Z"
        }
      ]
    }
  ]
}
```

### 5. Get Specific Receipt (`/receipts/<receipt_id>`)

**Method**: GET  
**Content-Type**: application/json  

**Response**:
```json
{
  "receipt": {
    "id": "uuid-string",
    "receipt_file_id": "uuid-string",
    "purchased_at": "2023-09-10T14:23:45.000Z",
    "merchant_name": "ACME Supermarket",
    "total_amount": 42.99,
    "currency": "USD",
    "payment_method": "Credit Card",
    "tax_amount": 3.45,
    "receipt_number": "INV-12345",
    "file_path": "uploads/unique-filename.pdf",
    "created_at": "2023-10-15T12:35:12.345Z",
    "updated_at": "2023-10-15T12:35:12.345Z",
    "items": [
      {
        "id": "uuid-string",
        "receipt_id": "uuid-string",
        "item_name": "Milk",
        "quantity": 2,
        "unit_price": 3.99,
        "total_price": 7.98,
        "created_at": "2023-10-15T12:35:12.345Z"
      },
      {
        "id": "uuid-string",
        "receipt_id": "uuid-string",
        "item_name": "Bread",
        "quantity": 1,
        "unit_price": 4.50,
        "total_price": 4.50,
        "created_at": "2023-10-15T12:35:12.345Z"
      }
    ]
  }
}
```

### 6. List All Receipt Files (`/receipt-files`)

**Method**: GET  
**Content-Type**: application/json  

**Response**:
```json
{
  "receipt_files": [
    {
      "id": "uuid-string",
      "file_name": "receipt.pdf",
      "file_path": "uploads/unique-filename.pdf",
      "is_valid": true,
      "invalid_reason": null,
      "is_processed": true,
      "created_at": "2023-10-15T12:34:56.789Z",
      "updated_at": "2023-10-15T12:35:12.345Z"
    }
  ]
}
```

### 7. Get Specific Receipt File (`/receipt-files/<receipt_file_id>`)

**Method**: GET  
**Content-Type**: application/json  

**Response**:
```json
{
  "receipt_file": {
    "id": "uuid-string",
    "file_name": "receipt.pdf",
    "file_path": "uploads/unique-filename.pdf",
    "is_valid": true,
    "invalid_reason": null,
    "is_processed": true,
    "created_at": "2023-10-15T12:34:56.789Z",
    "updated_at": "2023-10-15T12:35:12.345Z"
  }
}
```

## Extraction Techniques

The system uses several techniques to extract information from receipts:

1. **OCR Processing**: Converts PDF pages to images and extracts text using Tesseract OCR
2. **Named Entity Recognition**: Uses SpaCy NLP to identify entities like organizations (merchant names)
3. **Regular Expression Patterns**: Identifies dates, amounts, receipt numbers, and other structured data
4. **Text Position Analysis**: Uses the typical position of information on receipts (e.g., merchant name typically at top)

## Error Handling

The system implements various error handling mechanisms:

- Validates PDF files before processing
- Checks for file existence at multiple points
- Handles duplicate file uploads
- Provides meaningful error messages for invalid requests
- Gracefully handles OCR failures

## Security Considerations

- File size limitations to prevent denial of service attacks
- Secure filename handling to prevent path traversal attacks
- Input validation for all API endpoints
- Prevention of duplicate processing

## Future Enhancements

Potential areas for improvement:

1. **Categorization**: Add automatic expense categorization
2. **Multi-language support**: Extend OCR capabilities to different languages
3. **Data export**: Provide functionality to export data in various formats (CSV, Excel)
4. **User authentication**: Add user accounts and authentication
5. **Batch processing**: Support uploading and processing multiple receipts at once
6. **Receipt template learning**: Improve extraction accuracy for repeated merchants

## Troubleshooting

Common issues and solutions:

- **OCR quality problems**: Ensure proper image resolution and contrast in scanned PDFs
- **Tesseract errors**: Verify Tesseract is properly installed and accessible
- **PDF conversion issues**: Check Poppler installation
- **Database errors**: Ensure proper permissions for SQLite database file
- **Missing dependencies**: Run `poetry install` to ensure all dependencies are installed