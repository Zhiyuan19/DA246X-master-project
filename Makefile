poxdir ?= /opt/pox/

OUT_LOG_CTRL_PLANE="./results/output_app.txt"
OUT_LOG_TEST_RESULT="./results/output_test_prog.txt"

topo:
	@echo "starting the topology! (i.e., running mininet)"
	sudo python ./topology/topology.py

app:
	@echo "starting the baseController!"
	cd $(poxdir) && python ./pox.py baseController 2>&1 | tee ${OUT_LOG_CTRL_PLANE} &

test_prog:
	@echo "starting mininet and test program!"
	sudo python ./topology/topology_test.py 2>&1 | tee ${OUT_LOG_TEST_RESULT}
test:
	make app
	make test_prog

clean:
	@echo "project files removed from pox directory!"
	sudo mn --link=tc --topo=mytopo
	sudo killall click
	kill $(shell sudo lsof -t -i:8080)
