# Soldering-Iron-Access-Control
Software that controls student access to soldering irons. Done in collaboration with QUT EESS (Electrical Engineering Student Society) and the QUT Technical services department. The purpose of the project is to ensure that only students who have recieved formal soldering training that is provided by QUT and are able to safely solder use the device. The secondary purpose is to hold students accountable for the cleanliness of work spaces around soldering irons.

Raspberry Pi interfaces with electrical relays (electromechanical switches) that turn the soldering irons on and off via their power supply. A student will swipe their student ID card at the card reader and their ID will be sent to a url that checks their ID against ID's of authorized users. A response will be sent depending on whether or not there is a match. If a match occurs, the relay will close ('ON' state) and the soldering iron will be powered and available for use.

Next stage of project that is still in development is to have students enter their information to a database that the aforementioned url is located via a keyboard interfaced with an arduino.
