import sys
from document_processor import DocumentProcessor

def test_docx(file_path):
    try:
        with open(file_path, 'rb') as f:
            processor = DocumentProcessor()
            result = processor.process_document(f)
            print("Document processed successfully!")
            print(f"Extracted text length: {len(result.get('text', ''))} characters")
            print("First 500 characters:")
            print(result.get('text', '')[:500])
    except Exception as e:
        print(f"Error processing document: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_docx.py <path_to_docx_file>")
        sys.exit(1)
    test_docx(sys.argv[1])
