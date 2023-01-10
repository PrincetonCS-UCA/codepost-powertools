Writing Scripts
===============

The codePost Powertools can be imported as a package and run in scripts that you
write yourself. To do so, simply import it:

.. code-block:: python

   import codepost_powertools as cptools

   # Remember to log in for all the methods to work!
   cptools.log_in_codepost()

You can check the :doc:`api` for all the available methods.

Examples
--------

Getting a mapping from submission ids to student emails
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Please see :func:`~codepost_powertools.grading.get_ids_mapping`.

.. code-block:: python

   # Also works with the actual codePost `Course` or `Assignment` objects
   course = ('COS126', 'F2022')
   assignment = 'Hello'
   ids = cptools.grading.get_ids_mapping(course, assignment)
   for student_email, submission_id in ids.items():
       # do something...

.. code-block:: python

   course = codepost.course.retrieve(...)
   assignment = codepost.assignment.retrieve(...)
   ids = cptools.grading.get_ids_mapping(
       course, assignment, include_all_students=True
   )
   for student_email, submission_id in ids.items():
       if submission_id is None:
           # this student did not have a submission for this assignment
           continue
       # do something...

.. code-block:: python

   # Saves the mapping as a csv file at "output/COURSE/ASSIGNMENT/file.csv"
   ids = cptools.grading.get_ids_mapping(
       course, assignment, save_file='file.csv'
   )
