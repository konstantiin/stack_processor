(defun fib(x)
     (setq fcur 1)
     (setq fprev 1)
     (loop 
       (setq fnew (+ fcur fprev))
       (setq fprev fcur)
       (setq fcur fnew)
       (when (< x fnew) (break)))
      (fnew))

(defun tackle_negative(x)
    (if (<= x 0) 
        -1 
        (fib x)))

(printi (tackle_negative (read)))
# return is used to break loop (mb change to break)