# mbta_display

A quick tkinter app which displays the predictions for Boston subway stops using mbta's V3 API similar to the information given by station arrival boards or in a navigation app. 

Uses the same criteria as the arrival boards at stations to define arriving (ARR) and boarding (BRD) trains. 

To change the stop simply change STOP_ID in main.py and then replace the children platform IDs. 

Currently set for Brookline Village Station in Brookline, MA.

Was developed as a quick solution to an issue and is not perfect (nor pretty). 

~~~
--------------------------
| Last Updated: 18:06:42 |
--------------------------

INBOUND:
       North Station                3 min
       North Station                9 min
OUTBOUND:
           Riverside                4 min
           Riverside               11 min
           Riverside               14 min
           Riverside               22 min
           Riverside               38 min
           Riverside               43 min
           Riverside               57 min
           Riverside               63 min
~~~
