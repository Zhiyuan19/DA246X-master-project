poxdir ?= /opt/pox/

# Complete the makefile as you prefer!
topo:
	@echo "starting the topology! (i.e., running mininet)"
	sudo python ./topology/topology.py

app:
	@echo "starting the baseController!"
# TODO: add path support
	cd /opt/pox && python pox.py baseController

test:
	@echo "starting test scenarios!"
# TODO: verify	
	python ./topology/testing.py

clean:
	@echo "project files removed from pox directory!"
	sudo mn --link=tc --topo=mytopo

