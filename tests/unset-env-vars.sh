for var in $(env | grep TEST_ | cut -d= -f1)
do
  unset $var
done
