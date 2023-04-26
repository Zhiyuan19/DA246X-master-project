poxdir ?= /opt/pox/

# Define variables for output log files
APP_LOG_FILE = ./results/output_app.txt
TEST_PROG_LOG_FILE = ./results/output_test_prog.txt

# Define function to run a command in a new terminal window
define run_in_terminal
	x-terminal-emulator --title="$(1)" -- bash -c "script -f $(2) -c '$(3)'; read -p 'Press ENTER to exit...' "
endef

topo:
	@echo "starting the topology! (i.e., running mininet)"
	sudo python ./topology/topology.py

app:
	@echo "starting the baseController!"
	$(call run_in_terminal,"baseController",$(APP_LOG_FILE),"python $(poxdir)/pox.py baseController")

test_prog:
	@echo "starting mininet and test program!"
	$(call run_in_terminal,"testProg",$(TEST_PROG_LOG_FILE),"sudo python ./topology/topology_test.py")

test:
	make app
	make test_prog

clean:
	@echo "project files removed from pox directory!"
	sudo mn --link=tc --topo=mytopo
