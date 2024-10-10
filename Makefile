poxdir ?= /home/videoserver/Desktop/pox/

OUT_LOG_CTRL_PLANE="./results/output_app.txt"
OUT_LOG_TEST_RESULT="./results/output_test_prog.txt"

topo:
	@echo "starting the topology! (i.e., running mininet)"
	sudo python ./topology/topology.py

app:
	@echo "starting the baseController!"

	#sudo cp ./applications/sdn/* /opt/pox/ext
	#sudo cp ./applications/nfv/* /opt/pox/ext
	#mkdir -p /opt/pox/ext/results
	cd $(poxdir) && python ./pox.py forwarding.l2_learning
	

clean:
	@echo "project files removed from pox directory!"
	sudo mn --link=tc --topo=mytopo
	sudo killall click
	kill $(shell sudo lsof -t -i:8080)
	sudo cp /opt/pox/ext/results/* ./results
