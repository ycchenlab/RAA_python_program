for i in 0 1 2 3 4 5 6 7 8 9
do
	python iccad22.py $1 $i 0 &
	python iccad22.py $1 $i 1 &
done

