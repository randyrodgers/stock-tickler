# Stock Tickler
Website allowing users to add listed stocks to their watch list and be alerted should that stock exceed/go under their desired watch price!

<p align = "center"><kbd><img src = "/images/home1.png"></kbd></p>

<p><strong>Stock Tickler's purpose:</strong><br> 
Allow users easy access to their favorite stocks much like Robinhood does, but be automatically notified of their stock's status, so users will not have to constantly worry about their stocks' status. </p>

<h3> Accessing Stock Tickler</h3>
<ul>
  <li>Download this project from Github</li>
  <li>Make sure you have python3 installed</li>
  <li>Create a virtual environment and pip install django==2.2</li>
  <li>pip install celery==4.4.2, matplotlib, pandas, pandas-datareader, bcrypt</li>
  <li>brew/apt-get install rabbitmq
  <li>Navigate to project level folder in terminal and run "python manage.py runserver"</li>
  <li>In a separate terminal instance, navigate to the project level folder and run "celery -A project worker -l info"</li>
  <li>In a third terminal instance, run "rabbitmq-server"</li>
  <li>Go to http://localhost:8000/ in your desired browser!</li>
  <li>Enjoy Stock Tickler!</li>
  <li>(Deployment coming soon...)</li>
</ul>

<h3>How Stock Tickler Works</h3>
<ol>
  <li>Login/Register to join the Stock Tickler community to save stocks to your watch list!</li>
  <br>
  <p align = "center"><kbd><img src = "/images/login_page.gif"></kbd></p>
 <li>The login/register page is equipped with validations to ensure data congruency</li>
  <br>
 <p align = "center"><kbd><img src = "/images/validate.gif"></kbd></p>
  <li>Once logged in, you have access to your watch list!</li>
  <br>
 <p align = "center"><kbd><img src = "/images/login.gif"></kbd></p>
  <li>Change your name, email, password easily at the bottom of the page. Just enter your password!</li>
  <br>
  <p align = "center"><kbd><img src = "/images/update1.gif"></kbd></p>
  <li>Change your stock watch_price easily! A corresponding email will be sent to your email to notify you of the change.</li>
  <br>
  <p align = "center"><kbd><img src = "/images/change_price.gif"></kbd></p>
  <p align = "center"><kbd><img src = "/images/change_wp_email.gif"></kbd></p>
  <li>Navigate to the Picker page to find other stocks to add</li>
  <br>
  <p align = "center"><kbd><img src = "/images/picker.png"></kbd></p>
  <li>There are validations to check if your given ticker symbol exists for a real stock</li>
  <br>
  <p align = "center"><kbd><img src = "/images/stock_validate.gif"></kbd></p>
  <li>If the stock is valid, let Stock Tickler work its magic and add it to your watchlist!</li>
  <br>
  <p align = "center"><kbd><img src = "/images/add_stock.gif"></kbd></p>
  <li>If the watch price for a stock in your watchlist is ever met, you will receive an email!</li>
  <br>
  <p align = "center"><kbd><img src = "/images/watch_price_email.png"></kbd></p>
</ol>
<h3>Logic Behind Stock Tickler</h3>
<ul>
  <li>Automated Emails</li>
  <ul>
    <li>In settings.py, specify the sender email account information, using django.core.mail backend</li>
    <li>Establish subject and message of email based on changed watch price for given stock</li>
    <li>Use Django email API's send_mail function with parameters of subject, message, sender email provided in settings.py, and recipient email obtained through user login</li>
  </ul>
  
```python3
###in settings.py###
with open( 'project/secrets.json', 'r' ) as secret_key_file:
    data = secret_key_file.read()
    obj = json.loads( data )
    EMAIL_HOST_PASSWORD = str( obj[ 'EMAIL_HOST_PASSWORD' ] )
    secret_key_file.close()
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = 'stockticklerCD@gmail.com'

###in views.py###
from project.settings import EMAIL_HOST_USER
from django.core.mail import send_mail

subject = "Change to " + stock.ticker + " Watch Price"
message = "You are receiving this email to confirm that you have changed your watch price for " + stock.ticker + " from $" + str(old_price) + " to $" + str(stock.watch_price) + ". You will now receive an email notification if the stock reaches your new watch price. Thanks for using Stock Tickler!"
receipient = str(User.objects.get(id = request.session['logged_user_id']).email)
send_mail(subject, message, EMAIL_HOST_USER, [receipient], fail_silently=False)
```
  <li>Retrieve Stock Data</li>
  <ul>
    <li>First, use ModelManager class in models.py to verify given ticker symbol is an actual ticker that exists</li>
    <li>Using pandas DataReader, scrape data of given ticker symbol from yahoo Finance, with start_date being set to 5 years ago by default and end_date being the present</li>
    <li>After cleaning the data for data anomalies, retrieve the latest price in the dataset and update the current_price attribute of the Stock model</li>
  </ul>
  
```python3
### helper functions ###
def get_data (ticker, start, end):
    return data.DataReader(ticker, 'yahoo', start, end)

def clean_data(stock_data, col, start, end):
    weekdays = pd.date_range(start = start, end = end)
    clean_data = stock_data[col].reindex(weekdays)
    return clean_data.fillna(method = 'ffill')

def get_stats(stock_data):
    return {
        'last_price': np.mean(stock_data.tail(1))
    }
    
### views.py function ###
errors = Stock.objects.find_stock_validator( request.POST )
if len( errors ) > 0:
    for value in errors.values():
        messages.error( request, value )
    return redirect( '/add_stock' )

stock_data = get_data(request.POST['ticker'], START_DATE, END_DATE)
cleaned_data = clean_data(stock_data, ADJ_CLOSE, START_DATE, END_DATE)
stock_stats = get_stats(cleaned_data)
current_stock_price = stock_stats['last_price']

```
  <li>Call Update Function Periodically for Stock Data</li>
  <ul>
    <li>Using JavaScript's window setInterval function, submit form containing refresh button (which calls update function) every minute</li>
    <li>Use jQuery's AJAX function to asynchronously update the frontend/backend for user stocks to get real-time data</li>
    <li>Employed use of partial html to update solely the table of watchlist stocks on the page</li>
  </ul>

```js
setInterval(function(){ 
    console.log('interval reached');
    $('#retrieve_stock_data').submit();
}, 60000);
$(document).on('submit', '#retrieve_stock_data', function() {
    $.ajax({
        type: $(this).attr('method'),
        url: $(this).attr('action'),
        data: $(this).serialize(),
        success: function (data) {
            $('#table_body').html(data);
        },
        error: function(data) {
            console.log("something went wrong");
        }
    });
    return false;
});
```
</ul>
