poxdir ?= /opt/pox/

# Complete the makefile as you prefer!
topo:
	@echo "starting the topology! (i.e., running mininet)"
	sudo python ./topology/topology.py

app:
	@echo "starting the baseController!"
	gnome-terminal -- bash -c "script -f ./results/output_app.txt -c 'python $(poxdir)/pox.py baseController'"

test_prog:
	@echo "starting mininet and test program!"
	gnome-terminal -- bash -c "script -f ./results/output_test_prog.txt -c 'sudo python ./topology/topology_test.py'"

test:
	make app
	make test_prog

clean:
	@echo "project files removed from pox directory!"
	sudo mn --link=tc --topo=mytopo

