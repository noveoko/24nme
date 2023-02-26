def main():
    logging.info('Starting the application')
    # your code here
    from flask import Flask, render_template

    app = Flask(__name__)

    @app.route('/')
    def home():
    print('App running...')
        return render_template('index.html')

    if __name__ == '__main__':
        app.run()



    import logging

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.info('Finished running the application')

if __name__ == '__main__':
    main()
