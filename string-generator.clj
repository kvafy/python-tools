(ns string-generator
  (:require [clojure.java.io :as io]))

(comment

  Input map of the following format is expected by the "generate" function:

  {:template "select @@@id@@@ from dual"
   :variables
     [{:name "id" :type :enumerate :params {:items (range 0 10)}}]}



  Execute as follows:

   (generate {:template "insert into t(id,type,value) values (@id@, @type@,@value@);"
              :variables
                [{:name "id"    :type :enumerate      :params {:items (range 0 1000)}}
                 {:name "type"  :type :random-items   :params {:items ["'x'" "'y'" "'z'"] :count 1}}
                 {:name "value" :type :random-items   :params {:items (range 0 100) :count 1}}]})
)


;;TODO combinations (:items, :join-fn)

(defn combinations
  "Generates all combinations of given items as a lazy sequence."
  [items]
  (if (= (count items) 1)
    (list (list) items)
    (let [head (first items)
          tail-combinations (lazy-seq (combinations (next items)))]
      (concat tail-combinations
              (map #(cons head %) tail-combinations)))))


;; supported types of variables
(defmulti varvals (fn [vardef] (:type vardef)))

(defmethod varvals :enumerate [{:keys [params] :as vardef}]
  (let [{:keys [items]} params]
    items))

(defmethod varvals :random-items [{:keys [params] :as vardef}]
  (let [{:keys [items count]} params]
    (take count (repeatedly (fn [] (rand-nth items))))))



(defn- varmap-seq [vardefs]
  (if (empty? vardefs)
    (list {})
    (let [vardef (first vardefs)
          varname (:name vardef)]
      (apply concat
        (for [varval (varvals vardef)]
          (map #(merge % {varname (str varval)})
               (varmap-seq (rest vardefs))))))))

(defn- materialize [template varmap]
  (reduce (fn [partial-result [varname varvalue]]
            (let [placeholder (str "@" varname "@")]
              (clojure.string/replace partial-result placeholder varvalue)))
          template
          varmap))

(defn- generate [{template :template vardefs :variables}]
  (map materialize (repeat template) (varmap-seq vardefs)))

(time
(let [input {:template "insert into t(id,type,value) values (@id@, @type@,@value@);"
             :variables
               [{:name "id"    :type :enumerate      :params {:items (range 1 10000001)}}
                {:name "type"  :type :random-items   :params {:items ["'x'" "'y'" "'z'"] :count 1}}
                {:name "value" :type :random-items   :params {:items (range 0 100) :count 1}}]}
      output-file "D:/data.txt"]
  (with-open [writer (io/writer output-file)]
    (doseq [line (generate input)]
      (.write writer line)
      (.newLine writer))))
)
