def get_attachments(id):
    try:
        with open('./test_file.pdf', 'rb') as f:
            content = f.read()
        return content
    except Exception as e:
        return {
            'error': f'Error reading file: {str(e)}',
            'status': 500
        }, 500
