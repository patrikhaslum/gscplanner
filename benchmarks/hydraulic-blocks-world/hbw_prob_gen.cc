#include <iostream>
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <fstream>
#include <cassert>

#define MAX_TOWER 100
#define MAX_NUM_PROBLEM 100
#define MAX_BLOCK_PER_TOWER 100
#define MAX_NUM_INITIAL_STATE_PER_PROBLEM 100

using namespace std;

int blocks[MAX_TOWER][MAX_NUM_PROBLEM], num_tower, num_tower_in_init_state;
ofstream shopfile;
ofstream tgenfile;
ofstream pddlfile;

void rand_blocks(int num) {
  int i, j, x;
  for (i=1; i<MAX_TOWER; i++) {
    blocks[i][0]=0;
    for (j=1; j<MAX_BLOCK_PER_TOWER; j++) {
      blocks[i][j]=-1;
    }
  }
  
  num_tower=0;

  for (i=1; i<=num; i++) {
    x=random() % (num_tower+1);
    if (x==0) {
      num_tower++;
      blocks[num_tower][0]=1;
      blocks[num_tower][1]=i;
    }
    else {
      blocks[x][0]++;
      blocks[x][blocks[x][0]]=i;
    }
  }

}

void rand_blocks2(int num) {
  int i, j, x;
  for (i=1; i<MAX_TOWER; i++) {
    blocks[i][0]=0;
    for (j=1; j<MAX_BLOCK_PER_TOWER; j++) {
      blocks[i][j]=-1;
    }
  }
  
  num_tower=0;

  for (i=1; i<=num; i++) {
    x=random() % (num_tower+1);
    if (x==0 && num_tower < num_tower_in_init_state) {
      num_tower++;
      blocks[num_tower][0]=1;
      blocks[num_tower][1]=i;
    }
    else {
      blocks[x][0]++;
      blocks[x][blocks[x][0]]=i;
    }
  }

}


void print_blocks_header(char *problem_name, int nb)
{
  shopfile<<"(in-package :shop2)"<<endl;
  shopfile<<";;---------------------------------------------"<<endl;
  shopfile<<"\n(defproblem "<<problem_name<<" blocks-hgn"<<endl;
/*
  tgenfile<<";;---------------------------------------------"<<endl;
  tgenfile<<"\n(defproblem "<<problem_name<<" blocks-normal"<<endl;
  pddlfile<<";;---------------------------------------------"<<endl;
  pddlfile<<"\n(define (problem "<<problem_name<<")" <<endl;
  pddlfile<<"(:domain blocks-normal)"<<endl;
  pddlfile<<"(:objects ";
  for(int i=1; i <= nb; ++i)
    pddlfile<<" b"<<i;
  pddlfile<<")"<<endl; */
}
  
void print_blocks_initial_shop(char *problem_name, int ni, int nb) 
{
  int i, j, k;
  //  shopfile<<"("<<endl;
  for(k=0;k<ni;k++)
    {
      // rand_blocks(nb);
      shopfile<<"gripper_empty"<<endl;

//      for (i = 1; i <= nb; i++) {
//	      shopfile<<"\t(block b"<<i<<")"<<endl;
 //     }
/*      for(i=1; i<=nb; ++i) {
	for (j=1; j<=nb; ++j) {
	  if (i != j) {
	    shopfile<<"\t(different b"<<i<<" b"<<j<<")"<<endl;
	  }
	}
      }*/

      for (i=1; i<=num_tower; i++) 
        {
          shopfile<<"block_on_piston "<<blocks[i][1]-1<<endl;
          shopfile<<"block_in_cylinder "<<blocks[i][1]-1<<" "<<i-1<<endl;
          for (j=2; j<=blocks[i][0]; j++) 
            {
              shopfile<<"block_in_cylinder "<<blocks[i][j]-1<<" "<<i-1<<endl;
              shopfile<<"block_on_block "<<blocks[i][j]-1<<" "<<blocks[i][j-1]-1<<endl;
            }
          //shopfile<<"block_in_cylinder "<<blocks[i][blocks[i][0]]-1<<" "<<i-1<<endl;
          shopfile<<"block_clear "<<blocks[i][blocks[i][0]]-1<<endl;
        }
      //shopfile<<")"<<endl;
    }
  //shopfile<<")"<<endl;
}

void print_blocks_initial_tgen(char *problem_name, int ni, int nb) 
{
  int i, j, k;
  for(k=0;k<ni;k++)
    {
      // rand_blocks(nb);
      tgenfile<<"("<<endl;
      tgenfile<<"\t(arm-empty)"<<endl;
      for(i=1; i<=nb; ++i) {
	for (j=1; j<=nb; ++j) {
	  if (i != j) {
	    tgenfile<<"\t(different b"<<i<<" b"<<j<<")"<<endl;
	  }
	}
      }

      for (i=1; i<=num_tower; i++) 
        {
          tgenfile<<"\t(on-table b"<<blocks[i][1]<<")";
          for (j=2; j<=blocks[i][0]; j++) 
            {
              tgenfile<<" (on b"<<blocks[i][j]<<" b"<<blocks[i][j-1]<<")";
            }
          tgenfile<<" (clear b"<<blocks[i][blocks[i][0]]<<")"<<endl;
        }
      tgenfile<<")"<<endl;
    }
}

void print_blocks_initial_pddl(char *problem_name, int ni, int nb) 
{
  int i, j, k;
  for(k=0;k<ni;k++)
    {
      // rand_blocks(nb);
      pddlfile<<"(:init"<<endl;
      pddlfile<<"\t(arm-empty)"<<endl;
      for(i=1; i<=nb; ++i) {
	for (j=1; j<=nb; ++j) {
	  if (i != j) {
	    pddlfile<<"\t(different b"<<i<<" b"<<j<<")"<<endl;
	  }
	}
      }

      for (i=1; i<=num_tower; i++) 
        {
          pddlfile<<"\t(on-table b"<<blocks[i][1]<<")";
          for (j=2; j<=blocks[i][0]; j++) 
            {
              pddlfile<<" (on b"<<blocks[i][j]<<" b"<<blocks[i][j-1]<<")";
            }
          pddlfile<<" (clear b"<<blocks[i][blocks[i][0]]<<")"<<endl;
        }
      pddlfile<<")"<<endl;
    }
}

void print_blocks_goal_shop() {
  int i, j, k;

  shopfile<<"goal"<<endl;

  for (i=1; i<=num_tower; i++) {
    shopfile<<"block_on_piston "<<blocks[i][1]-1<<endl;
    for (j=2; j<=blocks[i][0]; j++) {
      shopfile<<"block_on_block "<<blocks[i][j]-1<<" "<<blocks[i][j-1]-1<<endl;
    }
    //shopfile<<"block_clear "<<blocks[i][blocks[i][0]]-1<<endl;
  }
  shopfile<<"end"<<endl;
}

void print_blocks_goal_tgen(int nb) {
  int i, j, k;

  tgenfile<<"("<<endl;
  tgenfile<<"\t(arm-empty)"<<endl;

  for(i=1; i<=nb; ++i) {
    for (j=1; j<=nb; ++j) {
      if (i != j) {
	tgenfile<<"\t(different b"<<i<<" b"<<j<<")"<<endl;
      }
    }
  }

  for (i=1; i<=num_tower; i++) {
    tgenfile<<"\t(on-table b"<<blocks[i][1]<<")";
    for (j=2; j<=blocks[i][0]; j++) {
      tgenfile<<" (on b"<<blocks[i][j]<<" b"<<blocks[i][j-1]<<")";
    }
    tgenfile<<" (clear b"<<blocks[i][blocks[i][0]]<<")"<<endl;
  }
  tgenfile<<")"<<endl;
  tgenfile<<")\n\n"<<endl;
}

void print_blocks_goal_pddl(int nb) {
  int i, j, k;

  pddlfile<<"(:goal"<<endl;
  pddlfile<<"\t(and (arm-empty)"<<endl;

  for(i=1; i<=nb; ++i) {
    for (j=1; j<=nb; ++j) {
      if (i != j) {
	pddlfile<<"\t(different b"<<i<<" b"<<j<<")"<<endl;
      }
    }
  }

  for (i=1; i<=num_tower; i++) {
    pddlfile<<"\t(on-table b"<<blocks[i][1]<<")";
    for (j=2; j<=blocks[i][0]; j++) {
      pddlfile<<" (on b"<<blocks[i][j]<<" b"<<blocks[i][j-1]<<")";
    }
    pddlfile<<" (clear b"<<blocks[i][blocks[i][0]]<<")"<<endl;
  }
  pddlfile<<"))"<<endl;
  pddlfile<<")\n\n"<<endl;
}

int main(int argc, char *argv[]) {
    char *filename=new char[256];
    char *problemname=new char[256];

    int sd, current_problem, num_block, num_problem, num_initials;
              
    if (argc==1) {
        cout<<"too few arguments"<<endl;
        cout<<"use \"gen [num of blocks] <number of problems> <max. number of initial states> <seed>\""<<endl;
        cout<<"if not specified, default number of problems is 1, and seed is choosen at random"<<endl;
        exit(0);
    }
    else {
        num_block=atoi(argv[1]);
    }
    if (argc>2) 
      {
        num_problem=atoi(argv[2]);
        if (num_problem>MAX_NUM_PROBLEM) 
          {
            num_problem=10;
          }
      }
    else 
       num_problem=1;

   if (argc>3) 
     {
       num_initials=atoi(argv[3]);
       if (num_initials>MAX_NUM_INITIAL_STATE_PER_PROBLEM) 
         {
           num_initials=10;
         }
     }
   else 
      num_initials=1;

    if (argc>4) 
     {
       sd=atoi(argv[4]);
     }
    else 
     {
       sd=time(NULL);
     }
    srandom(sd);  /* initialize random number generator */
    
//    sprintf(filename, "hgn-blocks-%d.lisp", num_block);
//   shopfile.open(filename, ios::out);
//    assert(shopfile);


    for (current_problem=0; current_problem<num_problem; current_problem++) {
            
      sprintf(filename, "p%d_%d.hbw", num_block, current_problem+1);
      shopfile.open(filename, ios::out);
      assert(shopfile);

      //sprintf(filename, "problems/p%d_%d.pddl", num_block, current_problem+1);
      //pddlfile.open(filename, ios::out);
      //assert(pddlfile);

      //shopfile << current_problem+1<<endl;
      sprintf(problemname, "p%d_%d", num_block, current_problem+1);

      // DEFPROBLEM
//      print_blocks_header(problemname, num_block);

      // INITIAL STATE
      rand_blocks(num_block);
      num_tower_in_init_state = num_tower;
      shopfile << num_block << endl;
      shopfile << num_tower << endl;

      shopfile << "initial_state" << endl;
      print_blocks_initial_shop(problemname, 1, num_block);
//      print_blocks_initial_tgen(problemname, 1, num_block);
//      print_blocks_initial_pddl(problemname, 1, num_block);

      // GOALS
      rand_blocks2(num_block);
      print_blocks_goal_shop();
//      print_blocks_goal_tgen(num_block);
  //    print_blocks_goal_pddl(num_block);
    
//      shopfile<<"(find-plans '" <<problemname<<" :verbose :stats :which :first)"<<endl;

    /*
    for (current_problem=0; current_problem<num_problem; current_problem++) {
      sprintf(problemname, "p%d_%d", num_block, current_problem+1);
       shopfile<<"(find-plans '" <<problemname<<" :verbose :stats :which :first)"<<endl;
    }
    */
   
      tgenfile.close();
      pddlfile.close();
      shopfile.close();
    }
    return 0;
}

