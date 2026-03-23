def get_archive(id):

    print('\n\nGot request to "get_archive" with id:\n')
    print(id)

    try:
        with open('./test_archive.zip', 'rb') as f:
            content = f.read()
        return content
    except Exception as e:
        return {
            'error': f'Error reading file: {str(e)}',
            'status': 500
        }, 500
