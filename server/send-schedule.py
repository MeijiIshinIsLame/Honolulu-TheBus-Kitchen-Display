import requests
import socket
import time

IP = "192.168.88.244"
PORT = 5005
DURATION = 60

class Arrival:
    def __init__(self, html_text):
        #<a href='nextbus.asp?s=1003&r=122'><b>122<i> </i>ALAPAI TRANSIT CENTER VIA KAKAAKO</b><br><i>Eastbound<br>scheduled &middot; 7:57 AM</i></a></li>
        self.html_text = html_text
        self.route = self.get_route()
        self.direction = self.get_direction()
        self.status = self.get_status()
        self.arrival_time = self.get_arrival_time()
    
    def get_route(self):
        #<b>122<i>
        start = self.html_text.find('<b>') + len("<b>")
        end = self.html_text.find('<i>')
        if self.html_text[start:end]:
            return self.html_text[start:end]
        else:
            return "unknown"
            
    def get_direction(self):
        if "Eastbound" in self.html_text:
            return "Eastbound"
        elif "Westbound" in self.html_text:
            return "Westbound"
        else:
            return "unknown"
        
    def get_status(self):
        #<br>Bus 289 &#183; arriving in 4 minutes</i>
        #<br>scheduled (no GPS signal) &middot; 11:56 PM</i>
        if "arriving" in self.html_text:
            return "arriving"
        elif "scheduled" in self.html_text:
            return "scheduled"
        else:
            return "unknown"
            
    def get_arrival_time(self):
        #<br>Bus 289 &#183; arriving in 4 minutes</i>
        #<br>scheduled &middot; 4:58 AM</i></a></li>
        if self.status == "arriving":
            start = self.html_text.find("arriving in ") + len("arriving in ")
            end = self.html_text.find(" minutes")
            return self.html_text[start:end]
        elif self.status == "scheduled":
            start = self.html_text.find("scheduled &middot; ") + len("scheduled &middot; ")
            end = self.html_text.find("</i></a></li>")
            return self.html_text[start:end]
        else:
            return "unknown"
            
    def __str__(self):
        return f"Route: {self.route}\nDirection: {self.direction}\nStatus: {self.status}\nArrival Time: {self.arrival_time}"
                

class Schedule:
    def __init__(self, arrivals):
        self.arrivals = arrivals
    
    def remove_duplicate_routes(self):
        seen = set()
        output = []
        for arrival in self.arrivals:
            if (arrival.route, arrival.direction) not in seen:
                seen.add((arrival.route, arrival.direction))
                output.append(arrival)
        self.arrivals = output
                
    def filter_out_keyword(self, keyword):
        output = []
        for arrival in self.arrivals:
            if keyword not in str(arrival):
                output.append(arrival)
        self.arrivals = output          

    def __str__(self):
        output = ""
        for arrival in self.arrivals:
            output += f"{str(arrival)}\n\n"
        return output
            

#break down each html <li> into list to parse into an Arrival object
def listify_html(html_text):
    start = html_text.find('<ul>') + len("<ul>")
    end = html_text.find('</ul>')
    return html_text[start:end].split("<li>")


def build_arrival_packet(arrivals):
    data = ""
    for arrival in arrivals:
        data += str(arrival) + "\n\n"
    return data
            

#duration in seconds    
def send_data_for_duration(ip, port, data, duration):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    end_time = time.time() + duration
    b = data.encode()
    
    print(b)
    while time.time() < end_time:
        print(f"Sending to {ip}:{port} for {duration}s")
        sock.sendto(b, (ip, port))
        time.sleep(0.5)
    sock.close()
    
def update_data():
    inside_stops_req = requests.get('https://hea.thebus.org/nextbus.asp?s=1003')
    inside_stops_html = inside_stops_req.text
    outside_stops_req = requests.get('https://hea.thebus.org/nextbus.asp?s=2288')
    outside_stops_html = inside_stops_req.text

    arrivals = []
    inside_arrivals = listify_html(inside_stops_html)
    outside_arrivals = listify_html(outside_stops_html)

    for arrival in inside_arrivals:
        arrivals.append(Arrival(arrival))
    for arrival in outside_arrivals:
        arrivals.append(Arrival(arrival))
    schedule = Schedule(arrivals)
    schedule.filter_out_keyword("unknown")
    schedule.remove_duplicate_routes()
    schedule.filter_out_keyword("Eastbound")
    data = build_arrival_packet(schedule.arrivals)
    return data

if __name__ == "__main__": 
    while True:    
        data = update_data()
        if not data:
            data = "NULL DATA"
        send_data_for_duration(IP, PORT, data, DURATION)