# Convexbot - A Halite 3 bot

## Fun Was Had
I had a lot of fun with Halite 3, but I am officially retiring.  I ended up with a silver ranking.  I was so close to gold I could taste it, but I guess it wasn't meant to be.  I got to a point where I saw the work that it was going to take to get to that next level.  It would have involved scrapping some systems I had written, writing a bunch of new systems, and getting a better understanding of the overall meta.  At the end of the day, this is just a game (or is it?) and I couldn't justify spending the time it was going to take to make a better bot when I had other things to work on.

## A Couple Classes
I wrote two classes for this halite bot that I thought were pretty interesting.  

The grid class was a way to check the amount of halite in a particular area.  Should I have continuted working on Halite 3, this is where I would have spent more time.  In my mind, this was the eyes of the bot.  It was a way to get information from the field.

The navigation class was used to replace the naive navigate class that shipped with the starter bot.  Early on I had several problems with naive navigate.  I tried to hack my way around them.  Then, I just decided to write my own navigation class.  This turned out to be way more challenging than I thought it would be.  Most of the time that I spent with Halite 3 was spent here, and I still don't consider it finished.

## Random Bot
My code ended up with a bunch of what I call "magic numbers."  These are hard coded numbers that are used as parameters of the bot.  I don't really like doing this, but it seemed like a necessary evil.  Previous versions of my bot had a great many more than the final version ended up with.  Anyway, I had this idea to put my current bot up against 1 or 3 random bots.  These random bots would use randomly generated numbers in place of some of my magic numbers.  I wrote a script that would play my bot against these random bots.  If the random bots won, their winning randomly generated numbers were recorded.  While I did get some insights to a winning formula, I didn't go very far with this.  First of all, I got into a kind relational problem.  A high value of x ensures a better chance at victory, but only if there is a low value for y.  Sounds easy when dealing with 2 parameters, but when there are 5 or 6 it gets really complicated.  Secondly, I kind of thought that I was writing a simple sort of ML program.  And if that's what I was doing, why not just use an actual ML program?

