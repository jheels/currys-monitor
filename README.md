# Currys Monitoring System

Constantly having to refresh a product site just to be told it's not instock can be disheartening and a waste of time sitting at a screen all day.
Instead you could save hours of your day while being notified when a product is instock within seconds.

## What does it do?

<ul>
  <li> Simple script that will alert you once a product is back instock</li>
  <li> You add product IDs with a helper bot that was created with user-friendliness in mind</li>
  <li> Run the script in the background and let it monitor</li>
</ul>

## How does it work?

The script can monitor two different API endpoints depending if you want to monitor the site or their alternative endpoint.

### Monitoring Frontend:

This is known as checking if the product is instock on their webpage with an API.

<ul>
  <li> More accurate than the alternative endpoint</li>
  <li> Relatively slower to check stock due to rate limit (how many times you can refresh in a second)</li>
 </ul>
 
 ### Monitoring Backend:
 
 This is known as checking the stock of the product using their private API.
 
 <ul>
  <li> Shows exact product of loaded stock on site and stock that can be purchased</li>
  <li> Faster to monitor as there is no rate limit enforced</li>
  <li> Not as reliable as frontend monitoring as it can be false</li>
 </ul>
 
 ## Getting Started
 
 To get started you will only need
 
 <ul>
  <li> A Discord account with a webhook URL to send alerts to.</li>
  <li> Python 3.X installed on your system</li>
 </ul>
 
 ### How to use?
 
 <ol>
  <li> To begin using the script you need to first add your private client ID from your discord bot into the bottom of the script</li>
  <li> Once this is done you can start adding or removing some products to your alert system.</li>
  <li> Now run the <code>monitor.py</code> with your desired monitoring type given above and let it alert you</li>


<br></br>
<img src="https://cdn.discordapp.com/attachments/858821667081814056/1102760924076593152/image.png" width="500" height="375">
